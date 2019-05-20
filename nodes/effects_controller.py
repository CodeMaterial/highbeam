import os
import sys
sys.path.append(os.getcwd())  # Don't ask...

import logging
import CostumePy
import time
from led_harness import LedHarness


class Controller:

    def __init__(self, *effects):
        self.node = CostumePy.new_node("LED_Controller")
        self.effects = {}
        self.effects_stack = []
        self.harness = LedHarness()

        self.node.listen("launch_effect", self.launch_effect)
        self.node.listen("stop_effect", self.stop_effect)

        self.node.ui.add_text("effects_running", order=99)

        for i, effect in enumerate(effects):
            name = effect.__name__
            self.node.ui.add_text("%s_text" % name, name, order=i*4)
            self.node.ui.add_button("%s_launch" % name, "Launch", "launch_effect", data=name, order=i*4+1)
            self.node.ui.add_button("%s_stop" % name, "Stop", "stop_effect", data=name, order=i*4+2)
            self.node.ui.add_break("%s_break" % name, order=i * 4 + 3)
            self.effects[name] = effect

        self.update_ui()

    def update_ui(self):
        running = [e.__class__.__name__ for e in self.effects_stack]
        self.node.ui.get("effects_running")["text"] = "Effects Running: %s" % " -> ".join(running)
        self.node.ui.update()

    def stop_effect(self, msg):
        self.effects_stack = [e for e in self.effects_stack if e.__class__.__name__ != msg["data"]]
        self.update_ui()

    def launch_effect(self, msg):
        effect_name = msg["data"]
        if effect_name in self.effects:
            effect = self.effects[effect_name]
            e = effect()
            e.start_time = time.time()
            self.effects_stack.append(e)
            self.update_ui()
        else:
            logging.error("%s not found" % effect_name)

    def run(self):
        while self.node.running:
            for i, effect in enumerate(self.effects_stack):
                harness = effect.update(time.time()-effect.start_time, self.harness)
                if harness is not None:
                    self.harness = harness
                else:
                    del self.effects_stack[i]
                    self.update_ui()

            self.harness.render()


if __name__ == "__main__":

    from effects import Swirl, Alignment

    c = Controller(Swirl, Alignment)

    c.run()
