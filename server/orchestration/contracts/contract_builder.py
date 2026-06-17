from __future__ import annotations

from orchestration.planning.plan_schema import Contract, ExecutionPlan


class ContractBuilder:
    def build(self, plan: ExecutionPlan) -> list[Contract]:
        contracts: list[Contract] = []
        for consumer in plan.agents:
            for producer_id, fields in consumer.consumes_from.items():
                contracts.append(
                    Contract(
                        producer_id=producer_id,
                        consumer_id=consumer.id,
                        required_fields=list(fields),
                    )
                )
        return contracts

    def downstream_contracts(self, plan: ExecutionPlan, producer_id: str) -> list[Contract]:
        return [contract for contract in self.build(plan) if contract.producer_id == producer_id]
