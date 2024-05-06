import copy

from HashTable import *
from Truck import *
from TimeSimulator import *
import csv
from datetime import datetime

ONLY_TRUCK_TWO = ['3', '18', '36', '38']
DELAYED = ['6', '25', '28', '32']
TOGETHER = ['13', '14', '15', '16', '19', '20']
WAIT = ['9']


def read_package_data(csv_file):
    packageData = []
    with open(csv_file) as file:
        reader = csv.reader(file)
        for row in reader:
            packageId = str(row[0]).strip('\ufeff')
            address, city, state, zipCode, deadline, weight, notes = row[1:]
            status = "HUB"
            if packageId == "9":
                address = "410 S State St"
                zipCode = "84111"
            packageData.append((packageId, address, city, state, zipCode, deadline, weight, notes, status))
        hash_table = HashTable(len(packageData))
        for item in packageData:
            hash_table.insert(item[0], item)
    return hash_table


def read_distance_data(csv_file):
    edges = []
    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        firstRow = 0
        for row in reader:
            if firstRow == 0:
                destination = row[1:]
                firstRow += 1
            else:
                source = row[0]
                weights = row[1:]
                i = 0
                for dest in destination:
                    if weights[i] != '':
                        edges.append((source.split('\n', 1)[0], dest.split('\n', 1)[1].split(',', 1)[0], weights[i]))
                        i += 1
    return edges


def determineGroups(packageHashTable, distanceData):
    tenThirty = []
    eod = []
    counter = 1
    while counter < 41:
        package = packageHashTable.search(str(counter))
        # Split packages up by deadline
        if package[5] == "EOD":
            eod.append(package)
        else:
            tenThirty.append(package)
        counter += 1
    return tenThirty, eod


def getDistance(start, end, distanceData):
    # Loop through distance data looking for the coordinating points and return the distance between
    for route in distanceData:
        if route[0].strip() == start and route[1].strip() == end:
            return route[2]
        elif route[0].strip() == end and route[1].strip() == start:
            return route[2]
        else:
            pass
    return None


def greedyAlgorithm(packages, distanceData):
    startEndPoint = ("0", '4001 South 700 East', 'Salt Lake City', '84107', 'start', '0', '', 'HUB')
    load = []
    totalDistance = 0.0
    # Set closest distance and location to none, if none, set first package as closest, loop through all packages and choose the closest until limit is reached.
    closestLocation = None
    closestLocationDistance = None
    startLocation = startEndPoint
    packageCopy = packages.copy()

    for package in packages:
        if package[5] == "9:00 AM":
            load.append(package)
            closestLocation = package
            closestLocationDistance = getDistance(startEndPoint[1], closestLocation[1], distanceData)
            startLocation = closestLocation
        if package[5] == "10:30 AM" and package[0] in DELAYED:
            if closestLocation is None and closestLocationDistance is None and package not in load:
                closestLocation = package
                closestLocationDistance = getDistance(startLocation[1], package[1], distanceData)
            elif package not in load:
                tempDistance = getDistance(startLocation[1], package[1], distanceData)
                if closestLocationDistance > tempDistance:
                    closestLocation = package
                    closestLocationDistance = tempDistance

        elif package[5] == "10:30 AM":
            if closestLocation is None and closestLocationDistance is None and package not in load:
                closestLocation = package
                closestLocationDistance = getDistance(startLocation[1], package[1], distanceData)
            elif package not in load:
                tempDistance = getDistance(startLocation[1], package[1], distanceData)
                if closestLocationDistance > tempDistance:
                    closestLocation = package
                    closestLocationDistance = tempDistance

    while len(load) < 16 and len(load) < len(packages):
        for package in packages:
            # For first iteration starting from HUB, set closest to the first package on the list
            if closestLocation is None and closestLocationDistance is None and package not in load:
                closestLocation = package
                closestLocationDistance = getDistance(startLocation[1], package[1], distanceData)
            # For everything else, check to see if the distance is the closest
            elif package not in load:
                tempDistance = getDistance(startLocation[1], package[1], distanceData)
                if closestLocationDistance > tempDistance:
                    closestLocation = package
                    closestLocationDistance = tempDistance
            else:
                pass
        # Once looped, set start location as closestLocation, add to load, repeat process.
        load.append(closestLocation)
        totalDistance += float(closestLocationDistance)
        startLocation = closestLocation
        closestLocation = None
        closestLocationDistance = None

    return load, totalDistance


def determineBestRoute(packageLoad, packageHashTable, distanceData):
    startPoint = ("0", '4001 South 700 East', 'Salt Lake City', '84107', 'start', '0', '', 'HUB')

    # Use greedy algorithm, the nearest location, to determine route
    # Start by grouping all tenThirty packages
    bestEarlyRoute, totalDistance = greedyAlgorithm(packageLoad, distanceData)

    return bestEarlyRoute, totalDistance


def loadTrucks(packageHashTable, distanceData):
    tenThirty, eod = determineGroups(packageHashTable, distanceData)

    loadFirst = []
    loadSecond = []
    loadThird = []
    loadFourth = []

    putOnTruckTwo = []
    putOnTruckOne = []
    putOnTruckThree = []

    # Separate split packages by deadline into different trucks based off of special notes that are presaved in arrays
    # check to see if the packages in the tenThirty array are found in the only truck two array, if they are, add to an array called putOnTruckTwo
    for id in ONLY_TRUCK_TWO:
        for package in tenThirty:
            if package[0] == id:
                loadSecond.append(package)
                tenThirty.remove(package)

    # Check to see if package is delayed, if it is, add to array calle load second, which will be loaded on truck two.
    for id in DELAYED:
        for package in tenThirty:
            if package[0] == id and package not in putOnTruckTwo:
                loadSecond.append(package)
                tenThirty.remove(package)

    # Check see if packages need to be loaded together, if they do, add to loadFirst
    for id in TOGETHER:
        for package in tenThirty:
            if package[0] == id and package not in putOnTruckTwo:
                loadFirst.append(package)
                tenThirty.remove(package)
        for package in eod:
            if package[0] == id and len(putOnTruckOne) < 16:
                loadFirst.append(package)
                eod.remove(package)

    bestDistanceArrayFirstLoad = []
    bestDistanceArraySecondLoad = []
    firstLoadCopy = loadFirst.copy()
    secondLoadCopy = loadSecond.copy()

    for package in tenThirty:
        firstLoadCopy.append(package)
        secondLoadCopy.append(package)
        firstBestRoute, totalFirst = determineBestRoute(firstLoadCopy, packageHashTable, distanceData)
        secondBestRoute, totalSecond = determineBestRoute(secondLoadCopy, packageHashTable, distanceData)

        for pack in loadFirst:
            if package[1] == pack[1]:
                loadFirst.append(package)
                break
        for pack in loadSecond:
            if package[1] == pack[1]:
                loadSecond.append(package)
                break

        if totalSecond < totalFirst:
            if len(loadSecond) < 16 and package[0] != '9' and package not in loadFirst and package not in loadSecond:
                loadSecond.append(package)

        else:
            if len(loadFirst) < 16 and package[0] != '9' and package not in loadFirst and package not in loadSecond:
                loadFirst.append(package)
        firstLoadCopy = loadFirst.copy()
        secondLoadCopy = loadSecond.copy()

    for package in firstLoadCopy:
        if package in tenThirty:
            tenThirty.remove(package)
    for package in secondLoadCopy:
        if package in tenThirty:
            tenThirty.remove(package)

    # Looks for duplicates in the eod list and will add them to first list or second depending on whether there is a match, this will add no extra time to deliver.
    for package in eod:
        for pack in firstLoadCopy:
            if pack[1] == package[1] and len(firstLoadCopy) < 16 and package[0] != '9':
                firstLoadCopy.append(package)
                break
    for package in eod:
        for pack in secondLoadCopy:
            if pack[1] == package[1] and len(secondLoadCopy) < 16 and package[0] != '9':
                secondLoadCopy.append(package)
                break
    for package in firstLoadCopy:
        if package in eod:
            eod.remove(package)
    for package in secondLoadCopy:
        if package in eod:
            eod.remove(package)

    thirdLoadCopy = []
    secondTruckLoadTwo = []

    loadFirst = firstLoadCopy.copy()

    for package in eod:
        firstLoadCopy.append(package)
        thirdLoadCopy.append(package)
        firstBestRoute, totalFirst = determineBestRoute(firstLoadCopy, packageHashTable, distanceData)
        secondBestRoute, totalSecond = determineBestRoute(thirdLoadCopy, packageHashTable, distanceData)

        if package[0] == '9':
            loadThird.append(package)
        elif totalSecond < totalFirst and package[0] != '9':
            if len(loadThird) < 16:
                loadThird.append(package)
        else:
            if len(loadFirst) < 16 and package[0] != '9':
                loadFirst.append(package)
        thirdLoadCopy = loadThird.copy()
        firstLoadCopy = loadFirst.copy()

    for package in thirdLoadCopy:
        if package in eod:
            eod.remove(package)
    for package in firstLoadCopy:
        if package in eod:
            eod.remove(package)

    thirdLoadCopy = loadThird.copy()
    secondTruckLoadTwo = loadFourth.copy()

    for package in eod:
        thirdLoadCopy.append(package)
        secondTruckLoadTwo.append(package)
        firstBestRoute, totalFirst = determineBestRoute(thirdLoadCopy, packageHashTable, distanceData)
        secondBestRoute, totalSecond = determineBestRoute(secondTruckLoadTwo, packageHashTable, distanceData)

        if package[7] == 'Can only be on truck 2':
            loadFourth.append(package)
        elif totalSecond < totalFirst:
            if len(loadFourth) < 16:
                loadFourth.append(package)
        else:
            if len(loadThird) < 16:
                loadThird.append(package)
        thirdLoadCopy = loadThird.copy()
        secondTruckLoadTwo = loadFourth.copy()

    for package in thirdLoadCopy:
        if package in eod:
            eod.remove(package)
    for package in secondTruckLoadTwo:
        if package in eod:
            eod.remove(package)

    bestRouteForOne = determineBestRoute(firstLoadCopy, packageHashTable, distanceData)
    bestRouteForTwo = determineBestRoute(secondLoadCopy, packageHashTable, distanceData)
    bestRouteForThree = determineBestRoute(thirdLoadCopy, packageHashTable, distanceData)
    # bestRouteForFour = determineBestRoute(secondTruckLoadTwo, packageHashTable, distanceData)

    truckOne = bestRouteForOne[0]
    truckTwo = bestRouteForTwo[0]
    truckThree = bestRouteForThree[0]
    # truckFour = bestRouteForFour[0]

    return truckOne, truckTwo, truckThree


# TODO: Continue to make deliver packages work, i am passing in three trucks to make keeping track of time easier. work on printing the time correctly.
def deliverPackages(truckOne, truckTwo, truckThree, packageHashTable, distanceData, timeOfDay):
    startPoint = ("0", '4001 South 700 East', 'Salt Lake City', '84107', 'start', '0', '', 'HUB')
    startLocation = None

    firstStatus = False
    secondStatus = False
    thirdStatus = False

    firstUpdate = None
    secondUpdate = None
    thirdUpdate = None

    for package in truckOne.packages:
        packageHashTable.insert(package[0], (
            package[0], package[1], package[2], package[3], package[4], package[5], package[6], package[7],
            "Out for Delivery - Truck One"))

    for package in truckOne.packages:
        if startLocation is None:
            startLocation = package[1]
            distanceDriven = float(getDistance(startPoint[1], startLocation, distanceData))
            timeTaken = float(distanceDriven) / 18
            timeOfDay.advance_time(timeTaken * 3600)

            if datetime(2024, 4, 28, 8, 35) < timeOfDay.get_current_time() < datetime(2024, 4, 28, 9, 25) and firstStatus is False:
                firstUpdate = copy.deepcopy(packageHashTable)
                firstStatus = True
                for package in truckTwo.packages:
                    packageHashTable.insert(package[0], (
                        package[0], package[1], package[2], package[3], package[4], package[5], package[6], package[7],
                        "Out for Delivery - Truck Two"))
            packageHashTable.insert(package[0], (
                package[0], package[1], package[2], package[3], package[4], package[5], package[6], package[7],
                "Delivered - " + str(timeOfDay.get_current_time())))
            truckOne.setMilesDriven(distanceDriven)
        else:
            # Calculate time and distance between the start and end points, update hash table with delivery times and update truck miles driven
            distanceDriven = float(getDistance(startLocation, package[1], distanceData))
            timeTaken = float(distanceDriven) / 18
            timeOfDay.advance_time(timeTaken * 3600)
            # This below updates the hashtable value
            packageHashTable.insert(package[0], (
                package[0], package[1], package[2], package[3], package[4], package[5], package[6], package[7],
                "Delivered - " + str(timeOfDay.get_current_time())))
            truckOne.setMilesDriven(distanceDriven)

            if datetime(2024, 4, 28, 8, 35) < timeOfDay.get_current_time() < datetime(2024, 4, 28, 9,
                                                                                      25) and firstStatus is False:
                firstUpdate = copy.deepcopy(packageHashTable)
                firstStatus = True
                for pack in truckTwo.packages:
                    packageHashTable.insert(pack[0], (
                        pack[0], pack[1], pack[2], pack[3], pack[4], pack[5], pack[6], pack[7],
                        "Out for Delivery - Truck Two"))

            if datetime(2024, 4, 28, 9, 35) < timeOfDay.get_current_time() < datetime(2024, 4, 28, 10,
                                                                                      35) and secondStatus is False:
                secondUpdate = copy.deepcopy(packageHashTable)
                secondStatus = True
            if datetime(2024, 4, 28, 12, 3) < timeOfDay.get_current_time() < datetime(2024, 4, 28, 1,
                                                                                      12) and thirdStatus is False:
                thirdUpdate = copy.deepcopy(packageHashTable)
                thirdStatus = True

            startLocation = package[1]
    # Calculate time and distance back to hub from last package delivered.
    distanceToHub = float(getDistance(startPoint[1], startLocation, distanceData))
    truckOne.setMilesDriven(distanceToHub)
    timeTaken = float(distanceToHub) / 18
    timeOfDay.advance_time(timeTaken * 3600)
    truckOne.setFinishTime(timeOfDay)

    startPoint = ("0", '4001 South 700 East', 'Salt Lake City', '84107', 'start', '0', '', 'HUB')
    startLocation = None
    nineFive = TimeSimulator(datetime(2024, 4, 28, 9, 5, 0))

    for package in truckTwo.packages:
        packageHashTable.insert(package[0], (
            package[0], package[1], package[2], package[3], package[4], package[5], package[6], package[7],
            "Out for Delivery - Truck Two"))

    for package in truckTwo.packages:
        if startLocation is None:
            startLocation = package[1]
            distanceDriven = float(getDistance(startPoint[1], startLocation, distanceData))
            timeTaken = float(distanceDriven) / 18
            nineFive.advance_time(timeTaken * 3600)

            if datetime(2024, 4, 28, 8, 35) < nineFive.get_current_time() < datetime(2024, 4, 28, 9,
                                                                                     25) and firstStatus is False:
                firstUpdate = copy.deepcopy(packageHashTable)
                firstStatus = True

            packageHashTable.insert(package[0], (
                package[0], package[1], package[2], package[3], package[4], package[5], package[6], package[7],
                "Delivered - " + str(nineFive.get_current_time())))
            truckTwo.setMilesDriven(distanceDriven)
        else:
            # Calculate time and distance between the start and end points, update hash table with delivery times and update truck miles driven
            distanceDriven = float(getDistance(startLocation, package[1], distanceData))
            timeTaken = float(distanceDriven) / 18
            nineFive.advance_time(timeTaken * 3600)
            # This below updates the hashtable value
            packageHashTable.insert(package[0], (
                package[0], package[1], package[2], package[3], package[4], package[5], package[6], package[7],
                "Delivered - " + str(nineFive.get_current_time())))
            truckTwo.setMilesDriven(distanceDriven)

            if datetime(2024, 4, 28, 8, 35) < nineFive.get_current_time() < datetime(2024, 4, 28, 9,
                                                                                     25) and firstStatus is False:
                firstUpdate = copy.deepcopy(packageHashTable)
                firstStatus = True
            if datetime(2024, 4, 28, 9, 35) < nineFive.get_current_time() < datetime(2024, 4, 28, 10,
                                                                                     35) and secondStatus is False:
                secondUpdate = copy.deepcopy(packageHashTable)
                secondStatus = True
            if datetime(2024, 4, 28, 12, 3) < nineFive.get_current_time() < datetime(2024, 4, 28, 1,
                                                                                     12) and thirdStatus is False:
                thirdUpdate = copy.deepcopy(packageHashTable)
                thirdStatus = True

            startLocation = package[1]
    # Calculate time and distance back to hub from last package delivered.
    distanceToHub = float(getDistance(startPoint[1], startLocation, distanceData))
    truckTwo.setMilesDriven(distanceToHub)
    timeTaken = float(distanceToHub) / 18
    nineFive.advance_time(timeTaken * 3600)
    truckTwo.setFinishTime(nineFive)

    startPoint = ("0", '4001 South 700 East', 'Salt Lake City', '84107', 'start', '0', '', 'HUB')
    startLocation = None
    nextLoadTime = None
    finalLoadtime = None

    # if truckOne.finishTime.get_current_time() < truckTwo.finishTime.get_current_time():
    #     nextLoadTime = TimeSimulator(truckOne.finishTime.get_current_time())
    #     # finalLoadtime = truckTwo.finishTime.get_current_time()
    # else:
    nextLoadTime = TimeSimulator(truckTwo.finishTime.get_current_time())
        # finalLoadtime = truckOne.finishTime.get_current_time()

    for package in truckThree.packages:
        packageHashTable.insert(package[0], (
            package[0], package[1], package[2], package[3], package[4], package[5], package[6], package[7],
            "Out for Delivery - Truck Two Load Two"))

    for package in truckThree.packages:
        if startLocation is None:
            startLocation = package[1]
            distanceDriven = float(getDistance(startPoint[1], startLocation, distanceData))
            timeTaken = float(distanceDriven) / 18
            nextLoadTime.advance_time(timeTaken * 3600)

            if datetime(2024, 4, 28, 9, 5) < nextLoadTime.get_current_time() < datetime(2024, 4, 28, 9, 15) and firstStatus is False:
                firstUpdate = copy.deepcopy(packageHashTable)
                firstStatus = True
            packageHashTable.insert(package[0], (
                package[0], package[1], package[2], package[3], package[4], package[5], package[6], package[7],
                "Delivered - " + str(nextLoadTime.get_current_time())))
            truckTwo.setMilesDriven(distanceDriven)
        else:
            # Calculate time and distance between the start and end points, update hash table with delivery times and update truck miles driven
            distanceDriven = float(getDistance(startLocation, package[1], distanceData))
            timeTaken = float(distanceDriven) / 18
            nextLoadTime.advance_time(timeTaken * 3600)
            # This below updates the hashtable value
            packageHashTable.insert(package[0], (
                package[0], package[1], package[2], package[3], package[4], package[5], package[6], package[7],
                "Delivered - " + str(nextLoadTime.get_current_time())))
            truckTwo.setMilesDriven(distanceDriven)

            if datetime(2024, 4, 28, 8, 35) < nextLoadTime.get_current_time() < datetime(2024, 4, 28, 9,
                                                                                         25) and firstStatus is False:
                firstUpdate = copy.deepcopy(packageHashTable)
                firstStatus = True
            if datetime(2024, 4, 28, 9, 35) < nextLoadTime.get_current_time() < datetime(2024, 4, 28, 10,
                                                                                         35) and secondStatus is False:
                secondUpdate = copy.deepcopy(packageHashTable)
                secondStatus = True
            if datetime(2024, 4, 28, 12, 3) < nextLoadTime.get_current_time() < datetime(2024, 4, 28, 1,
                                                                                         12) and thirdStatus is False:
                thirdUpdate = copy.deepcopy(packageHashTable)
                thirdStatus = True

            startLocation = package[1]
    # Calculate time and distance back to hub from last package delivered.
    distanceToHub = float(getDistance(startPoint[1], startLocation, distanceData))
    truckTwo.setMilesDriven(distanceToHub)
    timeTaken = float(distanceToHub) / 18
    nextLoadTime.advance_time(timeTaken * 3600)
    truckTwo.setFinishTime(nextLoadTime)

    return firstUpdate, secondUpdate, thirdUpdate, truckOne, truckTwo, truckThree


def startDay(packageHashTable, distanceData):
    truckOne = Truck()
    truckOne.setTruckId(1)
    truckTwo = Truck()
    truckTwo.setTruckId(2)
    truckThree = Truck()
    truckThree.setTruckId(3)
    # truckFour = Truck()

    print("========================== Packages to Deliver ==========================")
    for i in range(1, 41):
        print(packageHashTable.search(str(i)))
    print('\n')
    print('Begin loading ...')

    timeOfDay = TimeSimulator(datetime(2024, 4, 28, 8, 0))

    # Load Packages onto truck
    truckOneLoad, truckTwoLoad, truckThreeLoad = loadTrucks(packageHashTable, distanceData)

    truckOne.addPackagesAndRoute(truckOneLoad)
    truckTwo.addPackagesAndRoute(truckTwoLoad)
    truckThree.addPackagesAndRoute(truckThreeLoad)

    firstUpdate, secondUpdate, thirdUpdate, doneOne, doneTwo, doneThree = deliverPackages(truckOne, truckTwo,
                                                                                          truckThree, packageHashTable,
                                                                                          distanceData, timeOfDay)

    printStatus(firstUpdate, '8:35 - 9:25 AM')
    printStatus(secondUpdate, '9:35 - 10:25 AM')
    printStatus(thirdUpdate, '12:05 - 1:12 PM')

    return doneOne, doneTwo, doneThree


def printStatus(packageHashTable, timeSlot):
    if packageHashTable is None:
        print('========================== ' + timeSlot + ' ==========================')
        print("All delivered!")
    else:
        print('========================== ' + timeSlot + ' ==========================')

        for i in range(1, 41):
            print(packageHashTable.search(str(i)))
        print('\n')


if __name__ == '__main__':
    distanceData = read_distance_data("destinations.csv")
    packageHashTable = read_package_data("packageCSV.csv")

    print("==============================================================")
    print("========================== Welcome! ==========================")
    print("==============================================================")
    print('\n')
    print("Would you like to start the day? \n Y or N")

    answer = str(input())

    doneOne = None
    doneTwo = None
    doneThree = None

    if answer.lower() == 'y':
        doneOne, doneTwo, doneThree = startDay(packageHashTable, distanceData)
    else:
        print("Bye, Have a great day!")
        exit()

    print("========================== All Delivered ==========================")
    printStatus(packageHashTable, "Final Update")

    print('======================== Truck Statistics =========================')
    print('========================== Truck One ==========================')
    print('Miles driven: ' + str(doneOne.getMilesDriven()) + '\n')
    print('========================== Truck Two ==========================')
    print('Miles driven: ' + str(doneTwo.getMilesDriven()) + '\n')
    print('========================== Truck Three ==========================')
    print('Miles driven: ' + str(doneThree.getMilesDriven()) + '\n')

    # startDay(packageHashTable, distanceData)


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
