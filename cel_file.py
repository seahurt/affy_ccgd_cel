import os
from struct import unpack


class CelFile(object):
    def __init__(self, celfile):
        self.cel_path = os.path.abspath(celfile)
        self.fp = open(self.cel_path, 'rb')

        self.magic_number = None
        self.version = None
        self.group_num = None
        self.group_pos = 0
        self.data_set_pos = None

        self.read_file_header()    # read magic number, version, group number, group pos
        self.header = self.read_data_header()  # general data headers
        self.parents = self.read_parent_header()  # parent file headers
        self.extra = self.read_extra()  # extra params, include array_id and barcode

        self.data_groups = []  # data groups list

    @property
    def array_id(self):
        return self.extra[0].get('parameters').get('affymetrix-array-id').get('value')

    @property
    def barcode(self):
        return self.extra[0].get('parameters').get('affymetrix-array-barcode').get('value')

    def read_file_header(self):
        self.fp.seek(0)
        self.magic_number = self.read_ubyte()
        self.version = self.read_ubyte()
        self.group_num = self.read_int()
        self.group_pos = self.read_uint()

    def read_data_header(self):
        header = dict()
        header['uid'] = self.read_string()
        header['guid'] = self.read_guid()
        header['datetime'] = self.read_datetime()
        if header['uid']:
            header['uid'] = header['uid'].decode('utf-8')
        if header['guid']:
            header['guid'] = header['guid'].decode('utf-8')
        if header['datetime']:
            header['datetime'] = header['datetime'].decode('utf-8')
        header['locale'] = self.read_locale()
        header['parameters'] = self.read_parameters()
        return header

    def read_extra(self):
        extra = []
        extra_size = self.read_int()
        for x in range(extra_size):
            extra.append(self.read_data_header())
        return extra

    def read_data_groups(self):
        self.fp.seek(self.group_pos)
        for x in range(self.group_num):
            self.data_groups.append(self.read_data_group())

    def read_data_group(self):
        group = dict()
        self.group_pos = self.read_uint()  # next group pos or 0
        self.data_set_pos = self.read_uint()  # next dataset
        group['data_set_count'] = self.read_int()
        group['name'] = self.read_wstring()
        group['data_set'] = []
        for x in range(group['data_set_count']):
            group['data_set'].append(self.read_data_set())
        return group

    def read_data_set(self):
        self.fp.seek(self.data_set_pos)
        dataset = dict()
        ele_pos = self.read_uint()  # first element pos
        self.data_set_pos = self.read_uint()  # next dataset pos or 1 byte past the end of the dataset
        dataset['name'] = self.read_wstring()
        dataset['params'] = self.read_parameters()
        dataset['col'] = self.read_uint()
        dataset['col_format'] = []
        for x in range(dataset['col']):
            dataset['col_format'].append((self.read_wstring(), self.read_byte(), self.read_int()))
        dataset['row'] = self.read_uint()
        dataset['data'] = self.read_data(ele_pos, dataset['row'], dataset['col_format'])
        return dataset

    def read_data(self, ele_pos, rown, col_format):
        self.fp.seek(ele_pos)
        data = {}
        for y in col_format:
            name, value_type, value_size = y
            data[name] = []
        for x in range(rown):
            for y in col_format:
                name, value_type, value_size = y
                data[name].append(self.read_data_value(value_type, value_size))
        return data

    def read_data_value(self, _type, size):
        if _type == 0:
            value = self.read_byte()
        elif _type == 1:
            value = self.read_ubyte()
        elif _type == 2:
            value = self.read_short()
        elif _type == 3:
            value = self.read_ushort()
        elif _type == 4:
            value = self.read_int()
        elif _type == 5:
            value = self.read_uint()
        elif _type == 6:
            value = self.read_float()
        elif _type == 7:
            value = self.read_string()
        elif _type == 8:
            value = self.read_wstring()
        else:
            value = self.fp.read(size)
        return value

    def read_string(self, pos=None):
        size = self.read_int()
        if size == 0:
            return None
        s = []
        for x in range(size):
            b = self.read_char()
            s.append(b)
        return b''.join(s)
        # s = unpack(f'{size}s', self.fp.read(size))[0]
        # return s

    def read_int(self, pos=None):
        return unpack('>i', self.fp.read(4))[0]

    def read_uint(self, pos=None):
        return unpack('>I', self.fp.read(4))[0]

    def read_byte(self, pos=None):
        return unpack('b', self.fp.read(1))[0]

    def read_ubyte(self):
        return unpack('B', self.fp.read(1))[0]

    def read_char(self):
        return unpack('c', self.fp.read(1))[0]

    def read_short(self):
        return unpack('>h', self.fp.read(2))[0]

    def read_ushort(self):
        return unpack('>H', self.fp.read(2))[0]

    def read_float(self):
        return unpack('>f', self.fp.read(4))[0]

    def read_double(self):
        return unpack('>d', self.fp.read(4))[0]

    def read_guid(self):
        return self.read_string()

    def read_datetime(self):
        return self.read_wstring()

    def read_locale(self):
        return self.read_wstring()

    def read_wstring(self):
        size = self.read_int()
        # print(size)
        if size == 0:
            return None
        s = []
        for x in range(size):
            s.append(self.read_wchar())
        return ''.join(s)

    def read_wchar(self):
        chrs = self.fp.read(2)
        return chrs.decode('utf-16-be')

    def read_value(self, raw=True):
        if raw:
            return self.read_string()

    def read_type(self):
        return self.read_wstring()

    def read_parameters(self):
        count = self.read_int()
        p_list = []
        for x in range(count):
            p_list.append(self.read_parameter())
        return {x[0]: {'type': x[1], 'value': x[2]} for x in p_list}

    def read_parameter(self):
        # value_type = self.read_byte()

        name = self.read_wstring()
        value = self.read_value()
        t = self.read_type()
        value = self.format_value(value, t)
        return name, t, value,

    @staticmethod
    def parse_2byte_string(value):
        if not value:
            return value

        return value.rstrip(b'\x00').decode('utf-16-be')

    def format_value(self, value, _type):
        if _type == 'text/plain':
            value = self.parse_2byte_string(value)
        elif _type == 'text/x-calvin-float':
            value = unpack('>f', value[:4])[0]
        elif _type == 'text/x-calvin-integer-8':
            value = unpack('>b', value[:1])[0]
        elif _type == 'text/x-calvin-unsigned-integer-8':
            value = unpack('>B', value[:1])[0]
        elif _type == 'text/x-calvin-integer-16':
            value = unpack('>h', value[:2])[0]
        elif _type == 'text/x-calvin-unsigned-integer-16':
            value = unpack('>H', value[:2])[0]
        elif _type == 'text/x-calvin-integer-32':
            value = unpack('>i', value[:4])[0]
        elif _type == 'text/x-calvin-unsigned-integer-32':
            value = unpack('>I', value[:4])[0]
        elif _type == 'text/ascii':
            value = value.strip(b'\x00').decode('utf-8')
        else:
            print(f'{_type} is not recognised')
        return value

    def read_parent_header(self):
        header_count = self.read_int()
        headers = []
        for x in range(header_count):
            headers.append(self.read_data_header())
        return headers

    def make_table(self, seq):
        # length = max([x[0] for x in seq])
        return '\n'.join(['{:>50}\t{}'.format(x[0], x[1]['value']) for x in seq])

    def parameters_table(self, header):
        c = []
        for x in header['parameters']:
            c.append([x, header['parameters'][x]])
        c.sort(key=lambda x: len(x[0]))
        return self.make_table(c)

