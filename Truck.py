import uuid


class Truck:

    def __init__(self):
        self.loadTime = None
        self.id = uuid.UUID
        self.driverId = None
        self.packages = []
        self.route = []
        self.milesDriven = 0
        self.finishTime = None

    def addPackagesAndRoute(self, packages):
        self.packages = packages
        # self.route = route

    def deliveredPackages(self, packageId, distanceDriven):
        for package in self.packages:
            if package[0] == packageId:
                self.packages.remove(package[0])
                self.milesDriven += distanceDriven

    def getId(self):
        return self.id

    def setDriverId(self, driverId):
        self.driverId = driverId

    def setLoadTime(self, loadTime):
        self.loadTime = loadTime

    def getLoadTime(self):
        return self.loadTime

    def setMilesDriven(self, milesToAdd):
        self.milesDriven += milesToAdd

    def getMilesDriven(self):
        return self.milesDriven

    def setFinishTime(self, finish):
        self.finishTime = finish

    def getFinishTime(self):
        return self.finishTime