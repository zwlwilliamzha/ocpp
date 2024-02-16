import asyncio
import logging
import time
from datetime import datetime

import websockets

from ocpp.v16 import ChargePoint as cp
from ocpp.v16 import call
from ocpp.v16.datatypes import SampledValue, MeterValue
from ocpp.v16.enums import RegistrationStatus, AuthorizationStatus, RemoteStartStopStatus

logging.basicConfig(level=logging.INFO)


class ChargePoint(cp):
    async def simulate_charging(self, id_tag, connector_id, transaction_id):
        input("Press to send BootNotificationPayload")
        request = call.BootNotificationPayload(charge_point_model="Optimus", charge_point_vendor="The Mobility House")
        response = await self.call(request)
        if response.status == RegistrationStatus.accepted:
            print("Connected to central system.")

            input("Press to send AuthorizePayload")
            request = call.AuthorizePayload(id_tag=id_tag)
            response = await self.call(request)
            if response.id_tag_info["status"] == AuthorizationStatus.accepted:
                print(f'Authorized {id_tag} for charging')

                input("Press to send RemoteStartTransactionPayload")
                request = call.RemoteStartTransactionPayload(id_tag=id_tag)
                response = await self.call(request)
                if response.status == RemoteStartStopStatus.accepted:
                    print(f'Accepted {id_tag} to start charging')

                    for i in range(0, 5):
                        input("Press to send MeterValuesPayload")
                        current_value = 6
                        request = call.MeterValuesPayload(connector_id=connector_id, meter_value=[
                            MeterValue(timestamp=datetime.utcnow().isoformat(), sampled_value=[
                                SampledValue(str(current_value + i), context="Sample.Periodic", format="Raw",
                                             measurand="Current.Import",
                                             phase="L1", location="Outlet", unit="A"),
                                SampledValue("0.0", context="Sample.Periodic", format="Raw", measurand="Current.Import",
                                             phase="L2",
                                             location="Outlet", unit="A"),
                                SampledValue("0.0", context="Sample.Periodic", format="Raw", measurand="Current.Import",
                                             phase="L3",
                                             location="Outlet", unit="A"),
                                SampledValue(str(current_value + i), context="Sample.Periodic", format="Raw",
                                             measurand="Current.Offered",
                                             location="Outlet", unit="A"),
                                SampledValue("240", context="Sample.Periodic", format="Raw", measurand="Voltage",
                                             phase="L1-N",
                                             location="Outlet", unit="V"),
                                SampledValue("0.0", context="Sample.Periodic", format="Raw", measurand="Voltage",
                                             phase="L2-N",
                                             location="Outlet", unit="V"),
                                SampledValue("0.0", context="Sample.Periodic", format="Raw", measurand="Voltage",
                                             phase="L3-N",
                                             location="Outlet", unit="V")
                            ])
                        ])
                        response = await self.call(request)
                        print("Forwarded meter values to central system")
                        time.sleep(5)

                    input("Press to send RemoteStopTransactionPayload")
                    request = call.RemoteStopTransactionPayload(transaction_id=transaction_id)
                    response = await self.call(request)
                    if response.status == RemoteStartStopStatus.accepted:
                        print(f'Accepted {id_tag} to end charging on transaction_id {transaction_id}')


async def main():
    async with websockets.connect(
            "ws://192.168.1.111/CP_5", subprotocols=["ocpp1.6"]
    ) as ws:
        cp = ChargePoint("CP_1", ws)
        await asyncio.gather(
            cp.start(),
            cp.simulate_charging("car1", 12345, 12345)
        )


if __name__ == "__main__":
    # asyncio.run() is used when running this example with Python >= 3.7v
    asyncio.run(main())
