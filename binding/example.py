# standard modules
import sys
import time
import logging

# ostinato modules - prepend 'ostinato.' to the module names when using
# an installed package i.e ostinato.core and ostinato.protocols.xxx
from core import ost_pb, DroneProxy
from protocols.mac_pb2 import mac
from protocols.ip4_pb2 import ip4, Ip4

host_name = '127.0.0.1'
tx_port_number = 1
rx_port_number = 1

# setup logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

drone = DroneProxy(host_name)

try:
    # connect to drone
    log.info('connecting to drone(%s:%d)' 
            % (drone.hostName(), drone.portNumber()))
    drone.connect()

    tx_port = ost_pb.PortIdList()
    tx_port.port_id.add().id = tx_port_number;

    rx_port = ost_pb.PortIdList()
    rx_port.port_id.add().id = rx_port_number;

    # verify tx and rx ports exist
    log.info('verifying tx_port %d' % tx_port.port_id[0].id)
    port_config_list = drone.getPortConfig(tx_port)
    log.info('-->' + port_config_list.__str__())
    if len(port_config_list.port) <= 0:
        log.error('invalid tx_port'
                + tx_port_number)
        sys.exit(1)

    log.info('verifying rx_port %d' % rx_port.port_id[0].id)
    port_config_list = drone.getPortConfig(rx_port)
    log.info('-->' + port_config_list.__str__())
    if len(port_config_list.port) <= 0:
        log.error('invalid rx_port'
                + rx_port_number)
        sys.exit(1)

    # add a stream
    stream_id = ost_pb.StreamIdList()
    stream_id.port_id.CopyFrom(tx_port.port_id[0])
    stream_id.stream_id.add().id = 1
    log.info('adding tx_stream %d' % stream_id.stream_id[0].id)
    drone.addStream(stream_id)

    # configure the stream
    stream_cfg = ost_pb.StreamConfigList()
    stream_cfg.port_id.CopyFrom(tx_port.port_id[0])
    s = stream_cfg.stream.add()
    s.stream_id.id = stream_id.stream_id[0].id
    s.core.is_enabled = 1
    s.control.num_packets = 5

    p = s.protocol.add()
    p.protocol_id.id = ost_pb.Protocol.kMacFieldNumber
    p.Extensions[mac].dst_mac = 0x001122334455
    p.Extensions[mac].src_mac = 0x00aabbccddee

    p = s.protocol.add()
    p.protocol_id.id = ost_pb.Protocol.kEth2FieldNumber

    p = s.protocol.add()
    p.protocol_id.id = ost_pb.Protocol.kIp4FieldNumber
    p.Extensions[ip4].src_ip = 0x01020304
    p.Extensions[ip4].dst_ip = 0x05060708
    p.Extensions[ip4].dst_ip_mode = Ip4.e_im_inc_host

    s.protocol.add().protocol_id.id = ost_pb.Protocol.kUdpFieldNumber
    s.protocol.add().protocol_id.id = ost_pb.Protocol.kPayloadFieldNumber

    log.info('configuring tx_stream %d' % stream_id.stream_id[0].id)
    drone.modifyStream(stream_cfg)

    # clear tx/rx stats
    log.info('clearing tx/rx stats')
    drone.clearStats(tx_port)
    drone.clearStats(rx_port)

    # start transmit
    log.info('starting transmit')
    drone.startTx(tx_port)

    # wait for transmit to finish
    log.info('waiting for transmit to finish ...')
    time.sleep(7)

    # get tx/rx stats
    log.info('retreiving stats')
    tx_stats = drone.getStats(tx_port)
    rx_stats = drone.getStats(rx_port)

    log.info('--> (tx_stats)' + tx_stats.__str__())
    log.info('--> (rx_stats)' + rx_stats.__str__())
    log.info('tx pkts = %d, rx pkts = %d' % 
            (tx_stats.port_stats[0].tx_pkts, rx_stats.port_stats[0].rx_pkts))

except Exception, ex:
    log.exception(ex)
    sys.exit(1)