import xml.etree.ElementTree as ET
import Definition_of_interface, Comm, binascii, serial, time, traceback


# 68 49 00 43 05 24 11 11 11 11 11 00 9f f5 10 00 25 05 03 00 50 04 02 00 01 20 21 02 00 1c 07 e2 0c 1b 00 00 00 03 00 20 21 02 00 00 00 10 02 00 00 00 20 02 00 00 01 10 2b b5 ce 97 39 21 fc 9c d8 37 27 82 2e 8d e3 b5 d7 9e 16

# 68 34 00 43 05 24 11 11 11 11 11 00 3B 1C 05 03 00 50 04 02 00 01 20 21 02 00 1C 07 E2 0C 1B 00 00 00 03 00 20 21 02 00 00 00 10 02 00 00 00 20 02 00 00 76 55 16


def Analysis(code):
    code = Comm.makelist(code)
    while 1:
        if code[0] == '68':
            break
    lenth = int(code[2] + code[1], 16)  # 长度
    Rectrlc_1 = ctrlc_1(Comm.dec2bin(int(code[3], 16)))  # 控制码
    code_remain = code[4:]
    SA_len_num = SASign(Comm.dec2bin(int(code_remain[0], 16)).zfill(8))
    global SA_num_len
    SA_num_len = code_remain[0:1 + SA_len_num]
    CA = code_remain[1 + SA_len_num:][0]
    HCS = code_remain[1 + SA_len_num:][1] + code_remain[1 + SA_len_num:][2]
    APDU = code_remain[1 + SA_len_num:][3:-3]
    Information(APDU[0], APDU[1], APDU[2:])


def Information(num, detail, APDU):
    if num == '01':
        print(num, '预链接请求')
    elif num == '81':
        print(num, '预链接响应')
    elif num == '02':
        print(num, '应用链接请求')
    elif num == '82':
        print(num, '应用链接响应')
    elif num == '03':
        print(num, '断开链接响应')
    elif num == '83':
        print(num, '断开链接请求')
    elif num == '05':
        print(num, '读取请求', end=' ')
        if detail == '01':
            print(detail, '读取一个对象属性请求(GetRequestNormal) ')
        elif detail == '02':
            print(detail, '读取若干个对象属性请求 (GetRequestNormalList) ')
            SequenceOfLen(APDU[1:])
            global LargeOAD
            LargeOAD = LargeOAD + '0000'
            ReturnMessage().reAPDUtype(num + detail + '00')
            ReturnMessage().head()
            print('返回项数量', relen)


        elif detail == '03':
            print(detail, '读取一个记录型对象属性请求 (GetRequestRecord) ')
            returnvalue = A_ResultRecord_SEQUENCE(APDU[1:5])
            global frozenSign, data_list
            if returnvalue == 0:
                # todo
                Event(APDU[1:])
                return 0
            if returnvalue == '5002':
                frozenSign = 1
            if returnvalue == '5004':
                frozenSign = 2
            reCSD = RSD(APDU[5:])

            RCSD(reCSD[0], reCSD[1:])
            print('LargeOAD', LargeOAD)
            print('返回项数量', relen)
            LargeOAD = str(returnvalue) + '0200' + hex(relen)[2:].zfill(2) + LargeOAD + '0101'
            # ReturnMessage().reAPDUtype(num + detail + '00')
            datatype = num + detail + '00'
            datatype = '8' + datatype[1:]
            datatype = datatype.replace(' ', '')
            LargeOAD = datatype + LargeOAD + Comm.list_append(data_list) + '0000'
            ReturnMessage().head()
            print('data_list', Comm.list_append(data_list))
            print('组成', LargeOAD)

        elif detail == '04':
            print(detail, '读取若干个记录型对象属性请求 (GetRequestRecordList) ')
        elif detail == '05':
            print(detail, '读取分帧响应的下一个数据块请求 (GetRequestNext) ')
        elif detail == '06':
            print(detail, '读取一个对象属性的 MD5 值 (GetRequestMD5) ')
        else:
            print('ERROR:05??')
    elif num == '85':
        if detail == '01':
            print(detail, '读取一个对象属性的响应(GetResponseNormal) ')
        elif detail == '02':
            print(detail, '读取若干个对象属性的响应 (GetResponseNormalList) ')
        elif detail == '03':
            print(detail, '读取一个记录型对象属性的响应 (GetResponseRecord) ')
        elif detail == '04':
            print(detail, '读取若干个记录型对象属性的响应 (GetResponseRecordList) ')
        elif detail == '05':
            print(detail, '分帧响应一个数据块 (GetResponseNext) ')
        elif detail == '06':
            print(detail, '读取一个对象属性的 MD5 值的响应 (GetResponseMD5) ')
        else:
            print('ERROR:85??')
    elif num == '06':
        print(num, '设置请求')
    elif num == '86':
        print(num, '设置响应')
    elif num == '07':
        print(num, '操作请求')
    elif num == '87':
        print(num, '操作响应')
    elif num == '08':
        print(num, '上报回应')
    elif num == '88':
        print(num, '上报请求')
    elif num == '10':
        print(num, '安全请求')
        if detail == '00':
            print('明文')
            seclen = int(APDU[0], 16)
            realAPDU = APDU[1:seclen + 1]
            left = APDU[seclen + 1:]
            SecType = left[0]
            if SecType == '01':
                Information(realAPDU[0], realAPDU[1], realAPDU[2:])
            else:
                print('非随机数')
        if detail == '01':
            print('密文')


def SequenceOfLen(remain):
    lenth = int(remain[0], 16)
    remain = remain[1:]
    while lenth > 0:
        A_ResultRecord_SEQUENCE(remain[0:4])
        remain = remain[4:]
        lenth -= 1


def A_ResultRecord_SEQUENCE(remain):
    OAD = str(remain[0] + remain[1])
    if OAD == '5004' or OAD == '5002':
        print('冻结')
        return OAD
    if OAD[0] == '3':
        return 0
    else:
        OAD_SEQUENCE(OAD, remain[2], remain[3])


def Event(APDU):  # todo
    global LargeOAD
    '''Selector'''
    message = '850300' + Comm.list2str(APDU[0:4])
    if APDU[4] == '09':
        print('事件响应', Comm.list2str(APDU[0:4]))
        last_n = APDU[5]
        RCSD_len = int(APDU[6], 16)
        message = message + APDU[6]
        remain = APDU[7:]
        while RCSD_len:
            RCSD_len -= 1
            message = message + Comm.list2str(remain[0:5])
            value = Comm.list2str(remain[1:5]).zfill(4)
            event_compose_data(value)
            remain = remain[5:]
        LargeOAD = message + '0101' + LargeOAD + '0000'
        ReturnMessage().head()
        print('组成', LargeOAD)
    else:
        print('其他')


def event_compose_data(OI):
    compose = open('source\\698data', 'r', encoding='UTF-8', errors='ignore')
    while 1:
        text = compose.readline()
        if not text:
            print('未找到数据标识!')
            break
        text = text.split(' ')
        if text[0] == OI:
            print('text', text)
            message = text[2]
            print('message', message[0:-1])
            global LargeOAD
            LargeOAD = LargeOAD + message[0:-1]
            break
    compose.close()


def A_ResultRecord_SEQUENCE_RSD(remain):
    try:
        OI = remain[0] + remain[1]
        unsigned11 = Comm.dec2bin(int(remain[2])).zfill(8)  # 特征值
        unsigned11 = int(unsigned11[0:4], 10)
        print(OI, '特征:', unsigned11)
    except:
        traceback.print_exc(file=open('bug.txt', 'a+'))


def RSD(remain):
    if remain[0] == '01':
        print('Selector 01')
        A_ResultRecord_SEQUENCE_RSD(remain[1:5])
        reMessage = Data(remain[5], remain[6:])
        global relen
        relen = 0
        return reMessage
    if remain[0] == '02':
        print('Selector 02')
        A_ResultRecord_SEQUENCE_RSD(remain[1:5])
        reMessage = Data(remain[5], remain[6:])
        reMessage = Data(reMessage[0], reMessage[1:])
        reMessage = Data(reMessage[0], reMessage[1:])
        relen = 0
        return reMessage
    if remain[0] == '09':
        print('Selector 09')


def RCSD(remain_len, args):
    lens = int(remain_len)
    print('lens', lens)
    while lens > 0:
        args = CSD_CHOICE(args)
        lens -= 1
    return args

# def RCSD_frozenSign(remain_len, args):
#     lens = int(remain_len)
#     print('lens', lens)
#     while lens > 0:
#         args = CSD_CHOICE(args[1:])
#         lens -= 1
#     return args


def CSD_CHOICE(args):
    type = args[0]
    if type == '00':
        # print('CSD:', type)
        OAD = str(args[1] + args[2])
        OAD_SEQUENCE(OAD, args[3], args[4])
        if args == []:
            print('CSD_CHOICE is NULL')
        return args[5:]
    elif type == '01':
        value = ROAD(args[1:])
        if value == []:
            print('CSD_CHOICE is NULL')
        return value
    else:
        print('ERRORS:CSD_CHOICE')


def OAD_SEQUENCE(OI, unsigned1, unsigned2):
    try:
        unsigned11 = Comm.dec2bin(int(unsigned1)).zfill(8)  # 特征值
        unsigned11 = int(unsigned11[0:4], 10)
        print(OI, '特征:', unsigned11, '索引:', unsigned2)
        unsigned1 = '属性 ' + unsigned1[1]
        value = str(OI).zfill(4) + unsigned1[-1].zfill(2) + str(unsigned2).zfill(2)
        ReturnMessage().sequence_of_len()
        global frozenSign
        if frozenSign != 0:
            ReturnMessage().composefrozen(value)
        else:
            ReturnMessage().compose_data(value)
    except:
        traceback.print_exc(file=open('bug.txt', 'a+'))


def OAD_SEQUENCE_old(OI, unsigned1, unsigned2):
    unsigned11 = Comm.dec2bin(int(unsigned1)).zfill(8)  # 特征值
    unsigned11 = int(unsigned11[0:4], 10)
    unsigned1 = '属性 ' + unsigned1[1]
    OIcount = str(OI)[0]
    if 5 <= int(OIcount) <= 7:
        for child in root[1]:
            for childern in child:  # Table
                for grandchildern in childern:  # Row
                    Data = grandchildern.find("Data")
                    try:
                        if Data.text == str(OI):
                            print(Data.text, end=' ')
                            global i
                            i = 0
                        i += 1
                        if i == 3:
                            print(Data.text, end=' ')
                            global x
                            x += 1
                        if x == 1:
                            try:
                                if Data.text[3] == unsigned1[3]:
                                    print(Data.text, '特征:', unsigned11, '索引:', unsigned2)
                                    x += 1
                            except:
                                pass
                    except:
                        pass
    if int(OIcount) < 5:
        for child in root[1]:
            for childern in child:  # Table
                for grandchildern in childern:  # Row
                    Data = grandchildern.find("Data")
                    try:
                        if Data.text == str(OI).zfill(4):
                            print(Data.text, unsigned1, end=' ')
                            global ii
                            ii = 0
                        ii += 1
                        if ii == 2:
                            print('class id :', Data.text)
                            Class_id(Data.text, unsigned1[3])
                        if ii == 3:
                            print(Data.text, '特征:', unsigned11, '索引:', unsigned2)
                            value = str(OI).zfill(4) + unsigned1[-1].zfill(2) + str(unsigned2).zfill(2)
                            ReturnMessage().sequence_of_len()
                            global frozenSign
                            if frozenSign != 0:
                                ReturnMessage().composefrozen(value)
                            else:
                                ReturnMessage().compose_data(value)
                            # print(value)
                    except:
                        traceback.print_exc(file=open('bug.txt', 'a+'))


def Data(DataDescribe, args):
    DataDescribe = str(int(DataDescribe, 16)).zfill(2)
    if DataDescribe == '00':
        print('NULL', DataDescribe)
        return args

    elif DataDescribe == '01':
        print('array:', DataDescribe, end=' ')
        len1 = int(args[0], 16)
        lenori = len1
        args = args[1:]
        while len1 > 0:
            args = Data(args[0], args[1:])
            len1 -= 1
            print('Data', args)
        return args
    elif DataDescribe == '02':
        print('structure: ', DataDescribe)
        len2 = int(args[0], 16)
        lenori = len2
        args = args[1:]
        print('len:', len2)
        while len2 > 0:
            args = Data(args[0], args[1:])
            len2 -= 1
            print('Data', args)

        return args
    elif DataDescribe == '03':
        print('bool:', DataDescribe)
    elif DataDescribe == '04':
        print('bit-string:', DataDescribe)
        value = Comm.list2str(args[1:3])
        print('value', Comm.list2str(value))
        return args[3:]
    elif DataDescribe == '05':
        print('double-long: ', DataDescribe)
        value = int(args[0] + args[1] + args[2] + args[3], 16)
        if value > 2147483647:
            value = Comm.Inverse_code(bin(value))
            value = int(value, 2) + 1
            value = -value
        print('value', value)
        return args[4:]
    elif DataDescribe == '06':  # 4byte
        print('double-long-unsigned: ', DataDescribe)
        value = int(args[0] + args[1] + args[2] + args[3], 16)
        if value > 2147483647:
            value = Comm.Inverse_code(bin(value))
            value = int(value, 2) + 1
            value = -value
        print('value', value)
        return args[4:]
    elif DataDescribe == '09':
        print('octet-string: ', DataDescribe)
    elif DataDescribe == '10':
        print('visible-string: ', DataDescribe)
    elif DataDescribe == '12':
        print('UTF8-string:', DataDescribe)
    elif DataDescribe == '15':
        print('integer:', DataDescribe)
    elif DataDescribe == '16':
        print('long: ', DataDescribe)
        value = int(args[0] + args[1], 16)
        if value > 32767:
            value = Comm.Inverse_code(bin(value))
            value = int(value, 2) + 1
            value = -value
        print('value', value)
        return args[2:]
    elif DataDescribe == '17':
        print('unsigned:', DataDescribe)
    elif DataDescribe == '18':
        print('long-unsigned:', DataDescribe)
        value = int(args[0] + args[1], 16)
        if value > 32767:
            value = Comm.Inverse_code(bin(value))
            value = int(value, 2) + 1
            value = -value
        print('value', value)
        return args[2:]
    elif DataDescribe == '20':
        print('long64: ', DataDescribe)
    elif DataDescribe == '21':
        print('long64-unsigned', DataDescribe)
    elif DataDescribe == '22':
        print('enum', DataDescribe)
    elif DataDescribe == '23':
        print('float32', DataDescribe)
    elif DataDescribe == '24':
        print('float64', DataDescribe)
    elif DataDescribe == '25':
        print('date_time', DataDescribe)
    elif DataDescribe == '26':
        print('date', DataDescribe)
    elif DataDescribe == '27':
        print('time', DataDescribe)
    elif DataDescribe == '28':
        # print('date_time_s', DataDescribe)
        year = int(args[0] + args[1], 16)
        mouth = int(args[2], 16)
        day = int(args[3], 16)
        hour = int(args[4], 16)
        minute = int(args[5], 16)
        second = int(args[6], 16)
        datatime = str(year) + '年' + str(mouth) + '月' + str(day) + '日' + '   ' + str(hour).zfill(2) + ':' + str(
            minute).zfill(2) + ':' + str(
            second).zfill(2)
        print(datatime)
        print(args[7:])
        return args[7:]
    elif DataDescribe == '80':
        print('OAD ', DataDescribe)
    elif DataDescribe == '82':
        print('ROAD ', DataDescribe)
    elif DataDescribe == '83':
        print('OMD ', DataDescribe)
    elif DataDescribe == '84':
        print('TI', DataDescribe)
        timeUnit = int(args[0], 16)
        times = int(args[1] + args[2], 16)
        if timeUnit == 1:
            print(times, '分钟')
        return args[3:]
    elif DataDescribe == '85':
        print('TSA', DataDescribe)
        value = args[0:8]
        print('TSA', value)
        return args[8:]
    elif DataDescribe == '86':
        print('MAC', DataDescribe)
    elif DataDescribe == '87':
        print('RN', DataDescribe)
    elif DataDescribe == '88':
        print('Region', DataDescribe)
    elif DataDescribe == '89':
        print('Scaler_Unit ', DataDescribe)
    elif DataDescribe == '90':
        print('RSD', DataDescribe)
    elif DataDescribe == '91':
        print('CSD', DataDescribe)
    elif DataDescribe == '92':
        print('MS', DataDescribe)
    elif DataDescribe == '93':
        print('SID', DataDescribe)
    elif DataDescribe == '94':
        print('SID_MAC', DataDescribe)
    elif DataDescribe == '95':
        print('COMDCB', DataDescribe)
    elif DataDescribe == '96':
        print('RCSD', DataDescribe)
    else:
        print('ERROR on Data')


def SASign(num):
    numadd = int(str(num[0] + num[1]), 2)
    if numadd == 0:
        # print('0 单地址')
        pass
    elif numadd == 1:
        print('1 通配地址')
    elif numadd == 2:
        print('2 组地址')
    else:
        print('3 广播地址')
    # print(' 逻辑地址: ', num[2], num[3])
    numadd1 = int(num[4:], base=2)
    # print('地址长度 N: ', numadd1+1)
    return numadd1 + 1


def ctrlc_1(num):
    if num[0] == '0' and num[1] == '0':
        # print(num, 'DIR=0 PRM=0 客户机对服务器上报的响应')
        return 0
    elif num[0] == '0' and num[1] == '1':
        # print(num, 'DIR=0 PRM=1 客户机发起请求')
        return 1
    elif num[0] == '1' and num[1] == '0':
        # print(num, 'DIR=1 PRM=0 服务器发起上报')
        return 2
    else:
        # print(num, 'DIR=1 PRM=1 服务器对客户机请求的响应')
        return 3


def Class_id(classid, parameter):
    if classid == '1':
        Definition_of_interface.Definition_of_electric_energy_interface(parameter)


def SequenceOf_ARecordRow(data):
    global data_list
    data_list.append(data)


class ReturnMessage():
    def head(self):
        self.ctrlzone = 'c3'
        self.add = Comm.list2str(SA_num_len)
        self.CA = '00'
        self.totallenth()

    def totallenth(self):
        self.total = self.ctrlzone + self.add + self.CA
        global LargeOAD
        APDU_len = hex(len(Comm.makelist(LargeOAD)) + 6 + len(Comm.makelist(self.total)))[2:].zfill(2).zfill(4)
        print('APDUlen', APDU_len)

        self.head_message = Comm.strto0x(Comm.makelist(APDU_len[2:] + APDU_len[0:2] + self.total))
        self.HCS = str(hex(Comm.pppfcs16(0xffff, self.head_message, len(self.head_message)))).zfill(4)[2:]
        if len(self.HCS) == 3:
            self.HCS = '0' + self.HCS
        self.HCS = self.HCS[2:] + self.HCS[0:2]
        # print(self.HCS)
        LargeOAD = APDU_len[2:] + APDU_len[0:2] + self.total + self.HCS + LargeOAD

        self.full_message = Comm.strto0x(Comm.makelist(LargeOAD))
        self.FCS = str(hex(Comm.pppfcs16(0xffff, self.full_message, len(self.full_message)))).zfill(4)[2:]
        if len(self.FCS) == 3:
            self.FCS = '0' + self.FCS
        self.FCS = self.FCS[2:] + self.FCS[0:2]
        # print(self.FCS)
        LargeOAD = '68' + LargeOAD + self.FCS + '16'
        print('发送报文:', LargeOAD)
        global t
        t.write(binascii.a2b_hex(LargeOAD))

    def reAPDUtype(self, datatype):
        datatype = '8' + datatype[1:]
        self.datatype = datatype.replace(' ', '')
        global LargeOAD
        LargeOAD = self.datatype + hex(relen)[2:].zfill(2) + LargeOAD
        print('reapdu', self.datatype)

    def sequence_of_len(self):
        global relen
        relen += 1

    def compose_data(self, OI):
        compose = open('source\\698data', 'r', encoding='UTF-8', errors='ignore')
        while 1:
            text = compose.readline()
            if not text:
                print('未找到数据标识!')
                break
            text = text.split(' ')
            if text[0] == OI:
                print('text', text)

                if text[0] == '00100200':
                    global start_time
                    stop_time = int(time.time() - start_time)
                    OI_A = str(int(text[2][6:14]) + stop_time + 5).zfill(8)
                    OI_B = str(int(text[2][16:24]) + stop_time + 4).zfill(8)
                    OI_C = str(int(text[2][26:34]) + stop_time + 3).zfill(8)
                    OI_D = str(int(text[2][36:44]) + stop_time + 2).zfill(8)
                    OI_E = str(int(text[2][46:54]) + stop_time + 1).zfill(8)
                    text[2] = '010506' + OI_A + '06' + OI_B + '06' + OI_C + '06' + OI_D + '06' + OI_E + '0'
                self.message = text[0] + '01' + text[2]
                print('message', self.message[0:-1])
                global LargeOAD
                LargeOAD = LargeOAD + self.message[0:-1]

                break
        compose.close()

    def composefrozen(self, OI):
        compose = open('source\\698data', 'r', encoding='UTF-8', errors='ignore')
        while 1:
            text = compose.readline()
            text = text.split(' ')
            if text == '':
                print('未找到数据标识!')
                break
            global frozenSign
            if frozenSign == 1 and OI[0] != '5':
                newOI = '50020200_' + OI
            if frozenSign == 2 and OI[0] != '5':
                newOI = '50040200_' + OI
            if text[0] == newOI:
                print('text', text)
                SequenceOf_ARecordRow(text[2][0:-1])
                break
        compose.close()
        global LargeOAD
        LargeOAD = LargeOAD + '00' + OI


def start():
    global t
    t = serial.Serial('COM6', 2400, timeout=0.5, parity='E', stopbits=1)
    while 1:
        time.sleep(0.8)
        num = t.inWaiting()
        global data, relen, LargeOAD, frozenSign, data_list
        data = data + str(binascii.b2a_hex(t.read(num)))[2:-1]
        try:
            if data[0] == '6' and data[1] == '8':
                if data[-1] == '6' and data[-2] == '1':
                    print('Received: ', data)
                    Analysis(data.replace(' ', ''))

                    LargeOAD = ''
                    data_list = []
                    data = ''
                    relen = 0
                    frozenSign = 0

            else:
                continue
        except:
            continue


if __name__ == '__main__':
    # code = '68 49 00 43 05 24 11 11 11 11 11 00 9f f5 10 00 25 05 03 00 50 04 02 00 01 20 21 02 00 1c 07 e2 0c 1b 00 00 00 03 00 20 21 02 00 00 00 10 02 00 00 00 20 02 00 00 01 10 2b b5 ce 97 39 21 fc 9c d8 37 27 82 2e 8d e3 b5 d7 9e 16'
    # code = '68 20 00 43 05 02 00 00 00 00 00 00 e0 7d 05 02 00 03 00 10 02 00 00 20 02 00 20 21 02 00 00 7e c7 16'
    code = '685f00430504000000000000ab6710003b0503005002020002202102001c07e3010b001e001c07e3010b002c3b5401000f0500000002000000100200000020020000003002000020210200000110dbe874e868e2818062d57a7809720f39bfe616'
    asd = open('source\\output.xml', 'r', encoding='UTF-8', errors='ignore')
    tree = ET.parse(asd)
    root = tree.getroot()
    global start_time
    start_time = time.time()
    relen = 0
    LargeOAD = ''
    data = ''
    data_list = []
    frozenSign = 0

    Analysis(code.replace(' ', ''))
    # start()

'''
实时数据返回示例: 
68 42 00 c3 05 02 00 00 00 00 00 00 9a 3d 85 02 00 02 00 10 02 00 01 01 05 06 00 00 00 01 06 00 00 00 01 06 00 00 00 01 06 00 00 00 01 06 00 00 00 01 20 21 02 00 01 1c 07 e2 11 28 00 00 00 00 00 65 92 16
 '''
'''
日冻结返回示例:
68 68 00 c3 05 02 00 00 00 00 00 00 98 c8 85 03 00 50 04 02 00 03 00 00 10 02 00 00 00 20 02 00 00 20 21 02 00 01 01 01 05 06 00 00 00 33 06 00 00 00 34 06 00 00 00 35 06 00 00 00 36 06 00 00 00 37 01 05 06 00 00 00 44 06 00 00 00 45 06 00 00 00 46 06 00 00 00 47 06 00 00 00 48 1c 07 e2 0c 1a 00 00 00 00 00 d5 73 16
'''

'''
3011
68 24 00 43 05 02 00 00 00 00 00 00 b5 23 05 03 00 30 11 02 00 09 01 02 00 20 1e 02 00 00 20 20 02 00 00 8a 46 16 

68 35 00 C3 05 02 00 00 00 00 00 00 B6 C3 85 03 00 30 11 02 00 02 00 20 1E 02 00 00 20 20 02 00 01 01 1C 07 E1 02 02 03 02 11 1C 07 E1 02 02 04 02 04 00 00 C7 6B 16 
'''
