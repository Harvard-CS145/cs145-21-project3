from p4utils.utils.topology import Topology
from p4utils.utils.sswitch_API import SimpleSwitchAPI
import sys

class RoutingController(object):

    def __init__(self):
        self.topo = Topology(db="topology.db")
        self.controllers = {}
        self.init()

    def init(self):
        self.connect_to_switches()
        self.reset_states()
        self.set_table_defaults()

    def connect_to_switches(self):
        for p4switch in self.topo.get_p4switches():
            thrift_port = self.topo.get_thrift_port(p4switch)
            self.controllers[p4switch] = SimpleSwitchAPI(thrift_port)

    def reset_states(self):
        [controller.reset_state() for controller in self.controllers.values()]

    def set_table_defaults(self):
        # TODO: define table default actions

    def route(self):
        # TODO: define routing algorithm

    def main(self):
        self.route()


if __name__ == "__main__":
    controller = RoutingController().main()