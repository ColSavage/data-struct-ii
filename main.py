# Student ID: 011001848
# Hunter Tarkalson

import copy

from HashTable import *
from Truck import *
from TimeSimulator import *
import csv
from datetime import datetime, timedelta

ONLY_TRUCK_TWO = ['3', '18', '36', '38']
DELAYED = ['6', '25', '28', '32']
TOGETHER = ['13', '14', '15', '16', '19', '20']
WAIT = ['9']


# This function will read the package data found in the packagecsv file. it will also change the address for package 9 to the correct address. I will make sure not to do anything with it until after 10:20 am.
def read_package_data(csv_file):
    packageData = []
    with open(csv_file) as file:
        reader = csv.reader(file)
        for row in reader:
            packageId = str(row[0]).strip('\ufeff')
            address, city, state, zipCode, deadline, weight, notes = row[1:]
            status = "HUB"
            # if packageId == "9":
            #     address = "410 S State St"
            #     zipCode = "84111"
            packageData.append((packageId, address, city, state, zipCode, deadline, weight, notes, status))
        hash_table = HashTable(len(packageData))
        for item in packageData:
            hash_table.insert(item[0], item)
    return hash_table


# This function will read in the distance data from the distance csv file.
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


# Time: O(n)
# Space: O(n)
# This function will look at the deadline of each package and split them accordingly.
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


# Time: O(n)
# Space: O(n)
# This function will return the distance found in the distance data that was read in earlier.
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


# Time O(n^2)
# Space O(n)
# This is the nearest neighbor algorithm. I first set the starting point to the HUB, then I will look to see if any of the packages in the load need to be delivered earlier than others. The function compares distances and will choose the shortest unvisted path.
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
    # Use greedy algorithm, the nearest location, to determine route
    # Start by grouping all tenThirty packages
    bestEarlyRoute, totalDistance = greedyAlgorithm(packageLoad, distanceData)

    return bestEarlyRoute, totalDistance


# Time O(n^2)
# Space O(n)
# This function does the bulk of loading each truck. From this function, the nearest neighbor algorithm is called, it will first look to see which packages need to be on truck two, then the ones that are delayed and then the ones that need to be delivered together.
def newLoadTrucks(packageHashTable, distanceData):
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

    # For every package in tenThirty, see which truck load has will have the shortest delivery distance, add the package to the truck with shortest travel distance.
    for package in tenThirty:
        firstLoadCopy.append(package)
        secondLoadCopy.append(package)
        firstBestRoute, totalFirst = determineBestRoute(firstLoadCopy, packageHashTable, distanceData)
        secondBestRoute, totalSecond = determineBestRoute(secondLoadCopy, packageHashTable, distanceData)

        # see if address are the same i believe?
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

        # Resetting first and second load copies to update the list for calculating total distances
        firstLoadCopy = loadFirst.copy()
        secondLoadCopy = loadSecond.copy()

    # Remove the package from ten thirty if it was put on one of the two trucks
    for package in firstLoadCopy:
        if package in tenThirty:
            tenThirty.remove(package)
        if package in eod:
            eod.remove(package)
    for package in secondLoadCopy:
        if package in tenThirty:
            tenThirty.remove(package)
        if package in eod:
            eod.remove(package)

    # Looks for duplicates in the eod list and will add them to first list or second depending on whether there is a match, this will add no extra time to deliver.
    for package in eod:
        for pack in firstLoadCopy:
            if pack[1] == package[1] and package[0] not in DELAYED and len(firstLoadCopy) < 16 and package[0] != '9':
                firstLoadCopy.append(package)
                break
    for package in eod:
        for pack in secondLoadCopy:
            if pack[1] == package[1] and len(secondLoadCopy) < 16 and package[0] != '9':
                secondLoadCopy.append(package)

                break
    # Remove the package from eod if it was put on one of the two trucks
    for package in firstLoadCopy:
        if package in eod:
            eod.remove(package)
    for package in secondLoadCopy:
        if package in eod:
            eod.remove(package)

    thirdLoadCopy = []
    fourthLoadCopy = []
    secondTruckLoadTwo = []

    # Updating loadFirst so we can use it in the next bit
    loadFirst = firstLoadCopy.copy()
    loadSecond = secondLoadCopy.copy()

    for package in eod:
        for pack in secondLoadCopy:
            if pack[1] == package[1] and len(secondLoadCopy) < 16 and package[0] != '9':
                secondLoadCopy.append(package)
                break
    for package in secondLoadCopy:
        if package in eod:
            eod.remove(package)
    loadSecond = secondLoadCopy.copy()

    if len(eod) > 0:
        for package in eod:
            thirdLoadCopy.append(package)
            fourthLoadCopy.append(package)
            firstLoadCopy.append(package)
            bestRoute, total = determineBestRoute(firstLoadCopy, packageHashTable, distanceData)
            firstBestRoute, totalFirst = determineBestRoute(thirdLoadCopy, packageHashTable, distanceData)
            secondBestRoute, totalSecond = determineBestRoute(fourthLoadCopy, packageHashTable, distanceData)

            # see if address are the same i believe?
            for pack in loadFirst:
                if package[1] == pack[1]:
                    loadFirst.append(package)
                    break
            for pack in loadThird:
                if package[1] == pack[1]:
                    loadThird.append(package)
                    break
            for pack in loadFourth:
                if package[1] == pack[1]:
                    loadFourth.append(package)
                    break

            if totalSecond < totalFirst and totalSecond < total:
                if len(loadFourth) < 16 and package not in loadThird and package not in loadFourth and package not in loadFirst and \
                        package[0] not in ONLY_TRUCK_TWO:
                    loadFourth.append(package)
            elif total < totalFirst and total < totalSecond:
                if len(loadFirst) < 16 and package not in loadThird and package not in loadFourth and package not in loadFirst and \
                        package[0] not in ONLY_TRUCK_TWO:
                    loadFirst.append(package)
            elif totalFirst > total > totalSecond:
                if len(loadFourth) < 16 and package not in loadThird and package not in loadFourth and package not in loadFirst and \
                        package[0] not in ONLY_TRUCK_TWO:
                    loadFourth.append(package)
            elif totalFirst > totalSecond > total:
                if len(loadFirst) < 16 and package not in loadThird and package not in loadFourth and package not in loadFirst and \
                        package[0] not in ONLY_TRUCK_TWO:
                    loadFirst.append(package)
            else:
                if len(loadThird) < 16 and package not in loadThird and package not in loadFourth and package not in loadFirst:
                    loadThird.append(package)

            # Resetting first and second load copies to update the list for calculating total distances
            firstLoadCopy = loadFirst.copy()
            thirdLoadCopy = loadThird.copy()
            fourthLoadCopy = loadFourth.copy()

        for package in thirdLoadCopy:
            if package in eod:
                eod.remove(package)
        for package in fourthLoadCopy:
            if package in eod:
                eod.remove(package)
        for package in firstLoadCopy:
            if package in eod:
                eod.remove(package)

        if len(eod) > 0:
            for package in eod:
                if package[0] in ONLY_TRUCK_TWO:
                    secondLoadCopy.append(package)

    # Finalize the best routes for each load. Return the each load as truck one, two or three
    bestRouteForOne = determineBestRoute(firstLoadCopy, packageHashTable, distanceData)
    bestRouteForTwo = determineBestRoute(secondLoadCopy, packageHashTable, distanceData)
    bestRouteForThree = determineBestRoute(thirdLoadCopy, packageHashTable, distanceData)
    bestRouteForFour = determineBestRoute(fourthLoadCopy, packageHashTable, distanceData)

    truckOne = bestRouteForOne[0]
    truckTwo = bestRouteForTwo[0]
    truckThree = bestRouteForThree[0]
    truckFour = bestRouteForFour[0]

    return truckOne, truckTwo, truckThree, truckFour


# Checks to see if two different times are within a range of time (delta)
def is_within_range(time1, time2, delta):
    dummy_date = datetime(2024, 5, 30)
    datetime1 = datetime.combine(dummy_date, time1)
    datetime2 = datetime.combine(dummy_date, time2)

    return abs(datetime1 - datetime2) <= delta


# Time O(n)
# Space O(1)
# This function will deliver each package in each truck. It will update the hash table values as each package is delivered
def deliverPackages(truckOne, truckTwo, truckThree, truckFour, packageHashTable, distanceData, timeOfDay):
    startPoint = ("0", '4001 South 700 East', 'Salt Lake City', '84107', 'start', '0', '', 'HUB')
    startLocation = None

    firstStatus = False
    secondStatus = False
    thirdStatus = False

    firstUpdate = None
    secondUpdate = None
    thirdUpdate = None

    wasCorrected = False
    pastNineFive = False

    nineFiveHashTable = None

    arrayTruckOnUpdates = []
    arrayTruckTwoUpdates = []
    arrayTruckThreeUpdates = []
    arrayTruckFourUpdates = []
    # arrayTruckOnUpdates.append(packageHashTable)

    # Deliver packages in truck one
    for package in truckOne.packages:
        packageHashTable.insert(package[0], (
            package[0], package[1], package[2], package[3], package[4], package[5], package[6], package[7],
            "Out for Delivery - Truck One"))

    # Add updated hashtable to array to use to check updates
    arrayTruckOnUpdates.append((timeOfDay.get_current_time(), copy.deepcopy(packageHashTable)))

    for package in truckOne.packages:
        if startLocation is None:
            startLocation = package[1]
            distanceDriven = float(getDistance(startPoint[1], startLocation, distanceData))
            timeTaken = float(distanceDriven) / 18
            timeOfDay.advance_time(timeTaken * 3600)

            if timeOfDay.get_current_time() > datetime(2024, 4, 28, 10,
                                                       20) and wasCorrected is False:  # 410 S. State St., Salt Lake City, UT 84111
                for i in range(1, 41):
                    nine = packageHashTable.search(str(i))
                    if nine[0] == '9':
                        packageHashTable.insert(nine[0], (
                            nine[0], "410 S State St", nine[2], '84111', nine[4], nine[5], nine[6], nine[7], nine[8]))
                        wasCorrected = True

            if datetime(2024, 4, 28, 8, 35) < timeOfDay.get_current_time() < datetime(2024, 4, 28, 9,
                                                                                      25) and firstStatus is False:
                firstUpdate = copy.deepcopy(packageHashTable)
                firstStatus = True
                for pack in truckTwo.packages:
                    packageHashTable.insert(pack[0], (
                        pack[0], pack[1], pack[2], pack[3], pack[4], pack[5], pack[6], pack[7],
                        "Out for Delivery - Truck Two"))

            packageHashTable.insert(package[0], (
                package[0], package[1], package[2], package[3], package[4], package[5], package[6], package[7],
                "Delivered by T1 - " + str(timeOfDay.get_current_time())))
            truckOne.setMilesDriven(distanceDriven)

            # Check time to see if it is 9:05 yet, if so create copy of hash table to use
            if timeOfDay.get_current_time() > datetime(2024, 4, 28, 9, 5, 0) and nineFiveHashTable is None:
                nineFiveHashTable = copy.deepcopy(packageHashTable)

            # Add updated hashtable to array to use to check updates
            arrayTruckOnUpdates.append((timeOfDay.get_current_time(), copy.deepcopy(packageHashTable)))

        else:
            if timeOfDay.get_current_time() > datetime(2024, 4, 28, 10,
                                                       20) and wasCorrected is False:  # 410 S. State St., Salt Lake City, UT 84111
                for i in range(1, 41):
                    nine = packageHashTable.search(str(i))
                    if nine[0] == '9':
                        packageHashTable.insert(nine[0], (
                            nine[0], "410 S State St", nine[2], '84111', nine[4], nine[5], nine[6], nine[7], nine[8]))
                        wasCorrected = True
            # Calculate time and distance between the start and end points, update hash table with delivery times and update truck miles driven
            distanceDriven = float(getDistance(startLocation, package[1], distanceData))
            timeTaken = float(distanceDriven) / 18
            timeOfDay.advance_time(timeTaken * 3600)

            # Check time to see if it is 9:05 yet, if so create copy of hash table to use
            if timeOfDay.get_current_time() > datetime(2024, 4, 28, 9, 5, 0) and nineFiveHashTable is None:
                nineFiveHashTable = copy.deepcopy(packageHashTable)

            # This below updates the hashtable value
            packageHashTable.insert(package[0], (
                package[0], package[1], package[2], package[3], package[4], package[5], package[6], package[7],
                "Delivered by T1 - " + str(timeOfDay.get_current_time())))
            truckOne.setMilesDriven(distanceDriven)

            # Add updated hashtable to array to use to check updates
            arrayTruckOnUpdates.append((timeOfDay.get_current_time(), copy.deepcopy(packageHashTable)))
            startLocation = package[1]
    # Calculate time and distance back to hub from last package delivered.
    distanceToHub = float(getDistance(startPoint[1], startLocation, distanceData))
    truckOne.setMilesDriven(distanceToHub)
    timeTaken = float(distanceToHub) / 18
    timeOfDay.advance_time(timeTaken * 3600)
    truckOne.setFinishTime(timeOfDay)

    # Check time to see if it is 9:05 yet, if so create copy of hash table to use
    if timeOfDay.get_current_time() > datetime(2024, 4, 28, 9, 5, 0) and nineFiveHashTable is None:
        nineFiveHashTable = copy.deepcopy(packageHashTable)

    startPoint = ("0", '4001 South 700 East', 'Salt Lake City', '84107', 'start', '0', '', 'HUB')
    startLocation = None
    nineFive = TimeSimulator(datetime(2024, 4, 28, 9, 5, 0))
    wasCorrected = False
    # Deliver packages in truck two
    for package in truckTwo.packages:
        nineFiveHashTable.insert(package[0], (
            package[0], package[1], package[2], package[3], package[4], package[5], package[6], package[7],
            "Out for Delivery - Truck Two"))

    # Add updated hashtable to array to use to check updates
    arrayTruckTwoUpdates.append((nineFive.get_current_time(), copy.deepcopy(nineFiveHashTable)))
    for package in truckTwo.packages:
        if startLocation is None:
            startLocation = package[1]
            distanceDriven = float(getDistance(startPoint[1], startLocation, distanceData))
            timeTaken = float(distanceDriven) / 18
            nineFive.advance_time(timeTaken * 3600)
            if nineFive.get_current_time() > datetime(2024, 4, 28, 10,
                                                      20) and wasCorrected is False:
                for i in range(1, 41):
                    nine = packageHashTable.search(str(i))
                    if nine[0] == '9':
                        packageHashTable.insert(nine[0], (
                            nine[0], "410 S State St", nine[2], '84111', nine[4], nine[5], nine[6], nine[7], nine[8]))
                        wasCorrected = True
            if nineFive.get_current_time() > timeOfDay.get_current_time():
                packageHashTable.insert(package[0], (
                    package[0], package[1], package[2], package[3], package[4], package[5], package[6], package[7],
                    "Delivered by T2 - " + str(nineFive.get_current_time())))
            else:
                nineFiveHashTable.insert(package[0], (
                    package[0], package[1], package[2], package[3], package[4], package[5], package[6], package[7],
                    "Delivered by T2 - " + str(nineFive.get_current_time())))
            truckTwo.setMilesDriven(distanceDriven)

            # Add updated hashtable to array to use to check updates
            arrayTruckTwoUpdates.append((nineFive.get_current_time(), copy.deepcopy(nineFiveHashTable)))
        else:
            if nineFive.get_current_time() > datetime(2024, 4, 28, 10,
                                                      20) and wasCorrected is False:  # 410 S. State St., Salt Lake City, UT 84111
                for i in range(1, 41):
                    nine = packageHashTable.search(str(i))
                    if nine[0] == '9':
                        packageHashTable.insert(nine[0], (
                        nine[0], "410 S State St", nine[2], '84111', nine[4], nine[5], nine[6], nine[7], nine[8]))
                        wasCorrected = True
            # Calculate time and distance between the start and end points, update hash table with delivery times and update truck miles driven
            distanceDriven = float(getDistance(startLocation, package[1], distanceData))
            timeTaken = float(distanceDriven) / 18
            nineFive.advance_time(timeTaken * 3600)
            # This below updates the hashtable value
            nineFiveHashTable.insert(package[0], (
                package[0], package[1], package[2], package[3], package[4], package[5], package[6], package[7],
                "Delivered by T2 - " + str(nineFive.get_current_time())))
            truckTwo.setMilesDriven(distanceDriven)
            # Add updated hashtable to array to use to check updates
            arrayTruckTwoUpdates.append((nineFive.get_current_time(), copy.deepcopy(nineFiveHashTable)))
            startLocation = package[1]
    # Calculate time and distance back to hub from last package delivered.
    distanceToHub = float(getDistance(startPoint[1], startLocation, distanceData))
    truckTwo.setMilesDriven(distanceToHub)
    timeTaken = float(distanceToHub) / 18
    nineFive.advance_time(timeTaken * 3600)
    truckTwo.setFinishTime(nineFive)
    # Add updated hashtable to array to use to check updates
    arrayTruckTwoUpdates.append((nineFive.get_current_time(), copy.deepcopy(nineFiveHashTable)))

    startPoint = ("0", '4001 South 700 East', 'Salt Lake City', '84107', 'start', '0', '', 'HUB')
    startLocation = None
    nextLoadTime = None
    finalLoadtime = None

    nextLoadTime = TimeSimulator(truckTwo.finishTime.get_current_time())
    wasCorrected = False
    # Deliver packages in last load
    for package in truckThree.packages:
        pack = packageHashTable.search(package[0])
        packageHashTable.insert(pack[0], (
            pack[0], pack[1], pack[2], pack[3], pack[4], pack[5], pack[6], pack[7],
            "Out for Delivery - Truck Two Load Two"))
    # Add updated hashtable to array to use to check updates
    arrayTruckThreeUpdates.append((nextLoadTime.get_current_time(), copy.deepcopy(packageHashTable)))

    for package in truckThree.packages:
        if startLocation is None:
            startLocation = package[1]
            distanceDriven = float(getDistance(startPoint[1], startLocation, distanceData))
            timeTaken = float(distanceDriven) / 18
            nextLoadTime.advance_time(timeTaken * 3600)

            if datetime(2024, 4, 28, 9, 5) < nextLoadTime.get_current_time() < datetime(2024, 4, 28, 9,
                                                                                        15) and firstStatus is False:
                firstUpdate = copy.deepcopy(packageHashTable)
                firstStatus = True
            packageHashTable.insert(package[0], (
                package[0], package[1], package[2], package[3], package[4], package[5], package[6], package[7],
                "Delivered by T2 - " + str(nextLoadTime.get_current_time())))
            truckTwo.setMilesDriven(distanceDriven)
            # Add updated hashtable to array to use to check updates
            arrayTruckThreeUpdates.append((nextLoadTime.get_current_time(), copy.deepcopy(packageHashTable)))
        else:
            distanceDriven = float(getDistance(startLocation, package[1], distanceData))
            timeTaken = float(distanceDriven) / 18
            nextLoadTime.advance_time(timeTaken * 3600)
            # This below updates the hashtable value
            pack = packageHashTable.search(package[0])
            packageHashTable.insert(pack[0], (
                pack[0], pack[1], pack[2], pack[3], pack[4], pack[5], pack[6], pack[7],
                "Delivered by T2 - " + str(nextLoadTime.get_current_time())))
            truckTwo.setMilesDriven(distanceDriven)
            # Add updated hashtable to array to use to check updates
            arrayTruckThreeUpdates.append((nextLoadTime.get_current_time(), copy.deepcopy(packageHashTable)))
            startLocation = package[1]
        # Calculate time and distance back to hub from last package delivered.
    distanceToHub = float(getDistance(startPoint[1], startLocation, distanceData))
    truckTwo.setMilesDriven(distanceToHub)
    timeTaken = float(distanceToHub) / 18
    nextLoadTime.advance_time(timeTaken * 3600)
    truckTwo.setFinishTime(nextLoadTime)
    # Add updated hashtable to array to use to check updates
    arrayTruckThreeUpdates.append((nextLoadTime.get_current_time(), copy.deepcopy(packageHashTable)))

    startPoint = ("0", '4001 South 700 East', 'Salt Lake City', '84107', 'start', '0', '', 'HUB')
    startLocation = None
    nextLoadTime = None
    finalLoadtime = None

    nextLoadTime = TimeSimulator(truckOne.finishTime.get_current_time())
    wasCorrected = False
    if nextLoadTime.get_current_time() < datetime(2024, 4, 28, 10, 20) and wasCorrected is False:
        for i in range(1, 41):
            nine = packageHashTable.search(str(i))
            if nine[0] == '9':
                packageHashTable.insert(nine[0], (
                    nine[0], "300 State St", nine[2], '84103', nine[4], nine[5], nine[6], nine[7], nine[8]))
    # Deliver packages in last load
    for package in truckFour.packages:
        pack = packageHashTable.search(package[0])
        packageHashTable.insert(pack[0], (
            pack[0], pack[1], pack[2], pack[3], pack[4], pack[5], pack[6], pack[7],
            "Out for Delivery - Truck Three"))
    # Add updated hashtable to array to use to check updates
    arrayTruckFourUpdates.append((nextLoadTime.get_current_time(), copy.deepcopy(packageHashTable)))
    for package in truckFour.packages:
        if startLocation is None:
            startLocation = package[1]
            distanceDriven = float(getDistance(startPoint[1], startLocation, distanceData))
            timeTaken = float(distanceDriven) / 18
            nextLoadTime.advance_time(timeTaken * 3600)
            if nextLoadTime.get_current_time() > datetime(2024, 4, 28, 10, 20) and wasCorrected is False:
                for i in range(1, 41):
                    nine = packageHashTable.search(str(i))
                    if nine[0] == '9':
                        packageHashTable.insert(nine[0], (
                            nine[0], "410 S State St", nine[2], '84111', nine[4], nine[5], nine[6], nine[7], nine[8]))
                        wasCorrected = True
            if datetime(2024, 4, 28, 9, 5) < nextLoadTime.get_current_time() < datetime(2024, 4, 28, 9,
                                                                                        15) and firstStatus is False:
                firstUpdate = copy.deepcopy(packageHashTable)
                firstStatus = True
            packageHashTable.insert(package[0], (
                package[0], package[1], package[2], package[3], package[4], package[5], package[6], package[7],
                "Delivered by T3 - " + str(nextLoadTime.get_current_time())))
            truckThree.setMilesDriven(distanceDriven)
            # Add updated hashtable to array to use to check updates
            arrayTruckFourUpdates.append((nextLoadTime.get_current_time(), copy.deepcopy(packageHashTable)))
        else:
            distanceDriven = float(getDistance(startLocation, package[1], distanceData))
            timeTaken = float(distanceDriven) / 18
            nextLoadTime.advance_time(timeTaken * 3600)
            # This below updates the hashtable value
            pack = packageHashTable.search(package[0])
            packageHashTable.insert(pack[0], (
                pack[0], pack[1], pack[2], pack[3], pack[4], pack[5], pack[6], pack[7],
                "Delivered by T3 - " + str(nextLoadTime.get_current_time())))
            truckThree.setMilesDriven(distanceDriven)
            # Add updated hashtable to array to use to check updates
            arrayTruckFourUpdates.append((nextLoadTime.get_current_time(), copy.deepcopy(packageHashTable)))
            startLocation = package[1]

    truckThree.setFinishTime(nextLoadTime)
    # Add updated hashtable to array to use to check updates
    arrayTruckFourUpdates.append((nextLoadTime.get_current_time(), copy.deepcopy(packageHashTable)))
    return truckOne, truckTwo, truckThree, truckFour, arrayTruckOnUpdates, arrayTruckTwoUpdates, arrayTruckThreeUpdates, arrayTruckFourUpdates


# Function to calculate the difference in minutes
def time_difference(time1, time2):
    # Convert both times to datetime objects on the same day for comparison
    dummy_date = datetime(2000, 1, 1)
    datetime1 = datetime.combine(dummy_date, time1)
    datetime2 = datetime.combine(dummy_date, time2)
    return (datetime1 - datetime2).total_seconds() / 60


# This function will create all trucks, print the hashtable containing all packages and their data. It will then load each truck and then deliver alll packages.
# This function also allows for package look up. User can input an id or the work 'all' to display either a specific package or display all packages at an inputted time.
# To exit the application the user will type 'exit' and the application will end.
def startDay(packageHashTable, distanceData):
    truckOne = Truck()
    truckOne.setTruckId(1)
    truckTwo = Truck()
    truckTwo.setTruckId(2)
    truckThree = Truck()
    truckThree.setTruckId(3)
    truckFour = Truck()
    truckFour.setTruckId(4)

    print("========================== Packages to Deliver ==========================")
    for i in range(1, 41):
        print(packageHashTable.search(str(i)))
    print('\n')
    print('Begin loading ...')

    timeOfDay = TimeSimulator(datetime(2024, 4, 28, 8, 0))

    # Load Packages onto truck
    truckOneLoad, truckTwoLoad, truckThreeLoad, truckFourLoad = newLoadTrucks(packageHashTable, distanceData)

    truckOne.addPackagesAndRoute(truckOneLoad)
    truckTwo.addPackagesAndRoute(truckTwoLoad)
    truckThree.addPackagesAndRoute(truckThreeLoad)
    truckFour.addPackagesAndRoute(truckFourLoad)

    doneOne, doneTwo, doneThree, doneFour, arrayTruckOne, arrayTruckTwo, arrayTruckThree, arrayTruckFour = deliverPackages(
        truckOne, truckTwo,
        truckThree, truckFour,
        packageHashTable,
        distanceData,
        timeOfDay)
    done = False

    while done is False:
        print('====================== Check Status =================')
        print('Please enter the package ID or type all to see all packages at a given time. Type exit to end session:')
        pId = str(input())

        # if pId.lower() == 'exit':
        #     done = True
        #     break

        if pId.lower() != 'exit':
            print('Please enter a time: ')
            pTime = str(input())

            inputTime = datetime.strptime(pTime, '%H:%M').time()
        time_delta = timedelta(minutes=10)

        timeArrays = []

        if pId.lower() == 'all' or pId.lower() == 'exit':
            # Loop thru each array, filter by closest time then pull each item of each array that is closest to the inputted time. Then look for most recent update at that time.

            if pId.lower() == 'exit':
                pTime = '23:59'
                inputTime = datetime.strptime(pTime, '%H:%M').time()

            for instance in arrayTruckOne:
                instanceTime = instance[0].time()
                timeArrays.append((1, time_difference(instanceTime, inputTime), instance[1]))

            for instance in arrayTruckTwo:
                instanceTime = instance[0].time()
                timeArrays.append((2, time_difference(instanceTime, inputTime), instance[1]))

            for instance in arrayTruckThree:
                instanceTime = instance[0].time()
                timeArrays.append((3, time_difference(instanceTime, inputTime), instance[1]))

            for instance in arrayTruckFour:
                instanceTime = instance[0].time()
                timeArrays.append((4, time_difference(instanceTime, inputTime), instance[1]))

            filteredTimes = [match for match in timeArrays if match[1] <= 0]
            sorted_matches = sorted(filteredTimes, key=lambda x: abs(x[1]))

            first = False
            second = False
            third = False
            fourth = False

            startingTable = []
            hashTableCopy = copy.deepcopy(packageHashTable)

            for item in sorted_matches:
                # Set the starting table to display all packages. Set first, second, or third to true.
                if len(startingTable) == 0:
                    startingTable.append(item)
                    if item[0] == 1:
                        first = True
                    if item[0] == 2:
                        second = True
                    if item[0] == 3:
                        third = True
                    if item[0] == 4:
                        fourth = True
                else:
                    # if starting table is set, then look for the other trucks that have not had a chance to update the starting table.
                    if item[0] == 1 and first is False:
                        startingTable.append(item)
                        first = True
                    if item[0] == 2 and second is False:
                        startingTable.append(item)
                        second = True
                    if item[0] == 3 and third is False:
                        startingTable.append(item)
                        third = True
                    if item[0] == 4 and fourth is False:
                        startingTable.append(item)
                        third = True

            for element in hashTableCopy.values:
                # first set all packages in hashcopy to HUB to make comparisions easier
                pack = packageHashTable.search(element[0])
                hashTableCopy.insert(pack[0], (
                    pack[0], pack[1], pack[2], pack[3], pack[4], pack[5], pack[6], pack[7],
                    'HUB'))
            htCopyCopy = copy.deepcopy(hashTableCopy)
            updated = False
            # Now update the copy with updated statuses
            for load in startingTable:
                for item in load[2].values:
                    for element in hashTableCopy.values:
                        # for item in load[2].values:
                        if element[0] == item[0]:
                            if 'HUB' in item[8] and 'Delivered' not in element[8] and 'Out' not in element[8]:
                                pack = item
                                hashTableCopy.insert(pack[0], (
                                    pack[0], pack[1], pack[2], pack[3], pack[4], pack[5], pack[6], pack[7], item[8]))
                            elif element[0] == '9' and 'HUB' not in item[8] and updated is False:
                                pack = item
                                hashTableCopy.insert(pack[0], (
                                    pack[0], pack[1], pack[2], pack[3], pack[4], pack[5], pack[6], pack[7], item[8]))
                                updated = True
                            elif 'Delivered' not in element[8] and 'Delivered' in item[8]:
                                pack = packageHashTable.search(element[0])
                                hashTableCopy.insert(pack[0], (
                                    pack[0], pack[1], pack[2], pack[3], pack[4], pack[5], pack[6], pack[7], item[8]))
                            elif ('Out' not in element[8] and 'Delivered' not in element[8]) and 'Out' in item[8]:
                                pack = packageHashTable.search(element[0])
                                hashTableCopy.insert(pack[0], (
                                    pack[0], pack[1], pack[2], pack[3], pack[4], pack[5], pack[6], pack[7], item[8]))

            for i in range(1, 41):
                print(hashTableCopy.search(str(i)))

        else:
            pack = packageHashTable.search(pId)
            differences = []

            for i in range(0, len(doneOne.packages)):
                if pId == doneOne.packages[i][0]:
                    for instance in arrayTruckOne:
                        instanceTime = instance[0].time()
                        for p in instance[1].values:
                            if p[0] == pId:
                                differences.append((p, time_difference(instanceTime, inputTime)))

            for i in range(0, len(doneTwo.packages)):
                if pId == doneTwo.packages[i][0]:
                    for instance in arrayTruckTwo:
                        instanceTime = instance[0].time()
                        for p in instance[1].values:
                            if p[0] == pId:
                                differences.append((p, time_difference(instanceTime, inputTime)))

            for i in range(0, len(doneThree.packages)):
                if pId == doneThree.packages[i][0]:
                    for instance in arrayTruckThree:
                        instanceTime = instance[0].time()
                        for p in instance[1].values:
                            if p[0] == pId:
                                differences.append((p, time_difference(instanceTime, inputTime)))
            for i in range(0, len(doneFour.packages)):
                if pId == doneFour.packages[i][0]:
                    for instance in arrayTruckFour:
                        instanceTime = instance[0].time()
                        for p in instance[1].values:
                            if p[0] == pId:
                                differences.append((p, time_difference(instanceTime, inputTime)))

            filteredDifferences = [match for match in differences if match[1] <= 0]
            sorted_matches = sorted(filteredDifferences, key=lambda x: abs(x[1]))

            if len(sorted_matches) == 0:
                for i in range(0, len(doneOne.packages)):
                    for instance in arrayTruckOne:
                        instanceTime = instance[0].time()
                        for p in instance[1].values:
                            if p[0] == pId:
                                differences.append((p, time_difference(instanceTime, inputTime)))

            filteredDifferences = [match for match in differences if match[1] <= 0]
            sorted_matches = sorted(filteredDifferences, key=lambda x: abs(x[1]))

            print(sorted_matches[0][0])

            differences.clear()
        if pId.lower() == 'exit':
            done = True
            break

    return doneOne, doneTwo, doneThree, doneFour


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
        doneOne, doneTwo, doneThree, doneFour = startDay(packageHashTable, distanceData)
    else:
        print("Bye, Have a great day!")
        exit()

    print("========================== All Delivered ==========================")

    print('======================== Truck Statistics =========================')
    print('========================== Truck One ==========================')
    print('Miles driven: ' + str(doneOne.getMilesDriven()) + '\n')
    print('========================== Truck Two ==========================')
    print('Miles driven: ' + str(doneTwo.getMilesDriven()) + '\n')
    print('========================== Truck Three ==========================')
    print('Miles driven: ' + str(doneThree.getMilesDriven()) + '\n')

    totalMileage = doneOne.getMilesDriven() + doneTwo.getMilesDriven() + doneThree.getMilesDriven()

    print('============================= Total Mileage ========================')
    print(totalMileage)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
