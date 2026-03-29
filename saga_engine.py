#!/usr/bin/env python3
"""saga_engine - Saga pattern orchestrator with compensating transactions."""
import sys

class SagaStep:
    def __init__(self, name, action, compensate):
        self.name = name
        self.action = action
        self.compensate = compensate

class Saga:
    def __init__(self, steps):
        self.steps = steps
        self.completed = []
        self.log = []
    def execute(self, context):
        for step in self.steps:
            try:
                result = step.action(context)
                self.completed.append(step)
                self.log.append(("ok", step.name, result))
            except Exception as e:
                self.log.append(("fail", step.name, str(e)))
                self._compensate(context)
                return False, self.log
        return True, self.log
    def _compensate(self, context):
        for step in reversed(self.completed):
            try:
                step.compensate(context)
                self.log.append(("compensated", step.name, None))
            except Exception as e:
                self.log.append(("compensate_fail", step.name, str(e)))

def test():
    ctx = {"balance": 100, "reserved": False, "shipped": False}
    def reserve(c): c["reserved"] = True; return "reserved"
    def unreserve(c): c["reserved"] = False
    def charge(c):
        if c["balance"] < 50: raise ValueError("insufficient")
        c["balance"] -= 50; return "charged"
    def refund(c): c["balance"] += 50
    def ship(c): c["shipped"] = True; return "shipped"
    def unship(c): c["shipped"] = False
    s = Saga([SagaStep("reserve", reserve, unreserve), SagaStep("charge", charge, refund), SagaStep("ship", ship, unship)])
    ok, log = s.execute(ctx)
    assert ok
    assert ctx["balance"] == 50 and ctx["shipped"]
    ctx2 = {"balance": 30, "reserved": False, "shipped": False}
    s2 = Saga([SagaStep("reserve", reserve, unreserve), SagaStep("charge", charge, refund), SagaStep("ship", ship, unship)])
    ok2, log2 = s2.execute(ctx2)
    assert not ok2
    assert not ctx2["reserved"]  # compensated
    assert not ctx2["shipped"]
    print("saga_engine: all tests passed")

if __name__ == "__main__":
    test() if "--test" in sys.argv else print("Usage: saga_engine.py --test")
