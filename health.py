#!/usr/bin/python3


import dbus
from advertisement import Advertisement
from service import Application, Service, Characteristic, Descriptor
import pandas as pd

GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"
NOTIFY_TIMEOUT = 100


class HealthAdvertisement(Advertisement):
    def __init__(self, index):
        Advertisement.__init__(self, index, "peripheral")
        self.add_local_name("Health")
        self.include_tx_power = True


class HealthService(Service):
    HEALTH_SVC_UUID = "00000001-710e-4a5b-8d75-3e5b444bc3cf"

    def __init__(self, index):
        self.dataframe = pd.read_csv(
            r'/home/sinan/cputemp-master/bruxism_data.csv')
        self.count = 0
        Service.__init__(self, index, self.HEALTH_SVC_UUID, True)
        self.add_characteristic(HealthCharacteristic(self))

    def get_data(self):
        return self.dataframe

    def set_count(self, count):
        self.count = count

    def get_count(self):
        return self.count


class HealthCharacteristic(Characteristic):
    HEALTH_CHARACTERISTIC_UUID = "00000002-710e-4a5b-8d75-3e5b444bc3cf"

    def __init__(self, service):
        self.notifying = False
        Characteristic.__init__(
            self,
            self.HEALTH_CHARACTERISTIC_UUID,
            ["notify", "read"],
            service)
        self.add_descriptor(HealthDescriptor(self))

    def get_health_data(self):
        print("sinan")
        count = self.service.get_count()
        row = self.service.get_data().loc[count, :]
        self.service.set_count(count+1)
        value = []

        strtemp = str(row.to_json())
        for c in strtemp:
            value.append(dbus.Byte(c.encode()))

        return value

    def set_health_data_callback(self):
        if self.notifying:
            value = self.get_health_data()
            self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])

        return self.notifying

    def StartNotify(self):
        if self.notifying:
            return

        self.notifying = True
        value = self.get_health_data()
        self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])
        self.add_timeout(NOTIFY_TIMEOUT, self.set_health_data_callback)

    def StopNotify(self):
        self.notifying = False

    def ReadValue(self, options):
        value = self.get_health_data()

        return value


class HealthDescriptor(Descriptor):
    HEALTH_DESCRIPTOR_UUID = "2901"
    HEALTH_DESCRIPTOR_VALUE = "Health Data Temperature"

    def __init__(self, characteristic):
        Descriptor.__init__(
            self,
            self.HEALTH_DESCRIPTOR_UUID,
            ["read"],
            characteristic)

    def ReadValue(self, options):
        value = []
        desc = self.HEALTH_DESCRIPTOR_VALUE

        for c in desc:
            value.append(dbus.Byte(c.encode()))

        return value


app = Application()
app.add_service(HealthService(0))
app.register()

adv = HealthAdvertisement(0)
adv.register()

try:
    app.run()
except KeyboardInterrupt:
    app.quit()
