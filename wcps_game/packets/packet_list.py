from wcps_core.packets import PacketList as cp


class ClientXorKeys:
    SEND = 0x96
    RECEIVE = 0xC3


class PacketList:
    INTERNALGAMEAUTHENTICATION = cp.GameServerAuthentication
    INTERNALGAMESTATUS = cp.GameServerStatus
    INTERNALPLAYERAUTHENTICATION = cp.ClientAuthentication
