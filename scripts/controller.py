# This part gets rid of the 'Hello from PyGame...' message
from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame
from pygame.locals import *
import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.crazyflie.log import LogConfig
import logging
import numpy as np
import argparse
import os
from collections import deque
import time


# TODO: add these to argparse
# TODO: also add print statements to a new debug flag in argparse
takeoff_height = 0.3        # m
takeoff_velocity=0.2        # m/s
forward_vel = 0.2           # m/s
strafe_vel = 0.2            # m/s
turn_rate = 360.0 / 10.0    # rot/s
square_side = 0.4           # m
light_thresh = 1000         # lux (indoor light). Change to 100,000 lux for outdoors
dist_thresh = 220           # mm
sleep_time = 0.050          # sec
fwd_distance = 0.4          # m
flatness_threshold = 0.015  # m
vbat_threshold = 2.8        # V

is_FlowDeck_attached = True
checking_flatness = False
## Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)


#######################################
# Crazyflie functions
#######################################
def FlowDeckCheck(name, value):
    global is_FlowDeck_attached
    if value:
        is_FlowDeck_attached = True
        print('Flow Deck is attached!')
    else:
        is_FlowDeck_attached = False
        print('Flow Deck is NOT attached!')


def log_pos_callback(timestamp, data, logconf):
    '''
    Logging callback function for position
    '''
    # print("t={},x={},y={},z={},checking_flatness?={}\n".format(timestamp, data['stateEstimate.x'], data['stateEstimate.y'], data['stateEstimate.z'], checking_flatness))
    pos_file_handler.write("{},{},{},{},{}\n".format(timestamp, data['stateEstimate.x'], data['stateEstimate.y'], data['stateEstimate.z'], checking_flatness))
    if checking_flatness:
        global zrange
        zrange.append(data['stateEstimate.z'])


def log_range_callback(timestamp, data, logconf):
    '''
    Logging callback function for multiranger
    '''
    global range_left, range_front, range_right, range_back
    range_left, range_front, range_right, range_back = data['range.left'], data['range.front'], data['range.right'], data['range.back']
    # print("t={},left={},front={},right={},back={}\n"_format(timestamp, range_left, range_front, range_right, range_back))
    range_file_handler.write("{},{},{},{},{}\n".format(timestamp, range_left, range_front, range_right, range_back))


def log_intensity_callback(timestamp, data, logconf):
    '''
    Logging callback function for light intensity
    '''
    global intensity
    intensity = data['BH1750.intensity']
    print("t={},intensity={}".format(timestamp, intensity))
    intensity_file_handler.write("{},{}\n".format(timestamp, intensity))


def log_vbat_callback(timestamp, data, logconf):
    '''
    Logging callback function for battery voltage
    '''
    global vbat
    vbat = data['pm.vbat']
    print("t={}, vbat={} V".format(timestamp, vbat))
    vbat_file_handler.write("{},{}\n".format(timestamp, vbat))


def log_thrust_callback(timestamp, data, logconf):
    '''
    Logging callback function for thrust
    '''
    # print("t={}, thrust={} V".format(timestamp, data['stabilizer.thrust']))
    thrust_file_handler.write("{},{}\n".format(timestamp, data['stabilizer.thrust']))


def flatness_check(mc):
    global checking_flatness, flatness
    mc.stop()
    time.sleep(1)
    # Go to bottom-left corner of square
    mc.left(square_side/2, velocity=strafe_vel)
    mc.stop()
    mc.back(square_side/2, velocity=strafe_vel)
    mc.stop()
    time.sleep(1)
    # Start checking the flatness
    checking_flatness = True
    mc.forward(square_side, velocity=forward_vel)
    mc.stop()
    mc.right(square_side, velocity=strafe_vel)
    mc.stop()
    mc.back(square_side, velocity=strafe_vel)
    mc.stop()
    mc.left(square_side, velocity=strafe_vel)
    mc.stop()
    checking_flatness = False
    # Go back to the center of the square
    mc.forward(square_side/2, velocity=forward_vel)
    mc.stop()
    mc.right(square_side/2, velocity=strafe_vel)
    mc.stop()
    time.sleep(1)
    flatness = np.std(np.asarray(zrange))
    print("Standard deviation of zrange is: {}".format(flatness))
#######################################


if __name__ == '__main__':
    time.sleep(5)
    checking_flatness = False

    parser = argparse.ArgumentParser(description='Script to control the drone')
    parser.add_argument('-u', '--uri', type=str, default='69', help='URI of the crazyflie to connect to')
    # TODO: add flags to enable / disable logging of each log variable
    args = parser.parse_args()

    cflib.crtp.init_drivers(enable_debug_driver=False)

    with SyncCrazyflie('radio://0/'+args.uri+'/2M/E7E7E7E7E7', cf=Crazyflie(rw_cache=os.path.expanduser("~") + "/.cache")) as scf:
        scf.cf.param.add_update_callback(group="deck", name="bcFlow2", cb=FlowDeckCheck)

        # Logging position
        # Overwrite logfile contents
        pos_file_handler = open("../data/pos.csv", "w")
        pos_file_handler.close()
        pos_file_handler = open("../data/pos.csv", "a")
        logconf_pos = LogConfig(name='position', period_in_ms=10)
        logconf_pos.add_variable('stateEstimate.x', 'float')
        logconf_pos.add_variable('stateEstimate.y', 'float')
        logconf_pos.add_variable('stateEstimate.z', 'float')
        scf.cf.log.add_config(logconf_pos)
        logconf_pos.data_received_cb.add_callback(log_pos_callback)

        # Logging range
        # Overwrite logfile contents
        range_file_handler = open("../data/range.csv", "w")
        range_file_handler.close()
        range_file_handler = open("../data/range.csv", "a")
        logconf_range = LogConfig(name='range', period_in_ms=10)
        logconf_range.add_variable('range.front', 'float')
        logconf_range.add_variable('range.back', 'float')
        logconf_range.add_variable('range.left', 'float')
        logconf_range.add_variable('range.right', 'float')
        scf.cf.log.add_config(logconf_range)
        logconf_range.data_received_cb.add_callback(log_range_callback)

        # Logging intensity
        # Overwrite logfile contents
        intensity_file_handler = open("../data/intensity.csv", "w")
        intensity_file_handler.close()
        intensity_file_handler = open("../data/intensity.csv", "a")
        logconf_intensity = LogConfig(name='intensity', period_in_ms=200)
        logconf_intensity.add_variable('BH1750.intensity', 'float')
        scf.cf.log.add_config(logconf_intensity)
        logconf_intensity.data_received_cb.add_callback(log_intensity_callback)

        # Logging vbat
        # Overwrite logfile contents
        vbat_file_handler = open("../data/vbat.csv", "w")
        vbat_file_handler.close()
        vbat_file_handler = open("../data/vbat.csv", "a")
        logconf_vbat = LogConfig(name='vbat', period_in_ms=1000)
        logconf_vbat.add_variable('pm.vbat', 'float')
        scf.cf.log.add_config(logconf_vbat)
        logconf_vbat.data_received_cb.add_callback(log_vbat_callback)

        # Logging thrust
        # Overwrite logfile contents
        thrust_file_handler = open("../data/thrust.csv", "w")
        thrust_file_handler.close()
        thrust_file_handler = open("../data/thrust.csv", "a")
        logconf_thrust = LogConfig(name='thrust', period_in_ms=1000)
        logconf_thrust.add_variable('stabilizer.thrust', 'float')
        scf.cf.log.add_config(logconf_thrust)
        logconf_thrust.data_received_cb.add_callback(log_thrust_callback)

        intensity, range_left, range_front, range_right, range_back, vbat = 0, 0, 0, 0, 0, 0

        if is_FlowDeck_attached:
            mc = MotionCommander(scf, default_height=takeoff_height)
            mc.take_off(height=takeoff_height, velocity=takeoff_velocity)
            # with MotionCommander(scf, default_height=takeoff_height) as mc:
            time.sleep(1)
            # Start logging
            logconf_pos.start()
            logconf_range.start()
            logconf_intensity.start()
            logconf_vbat.start()
            logconf_thrust.start()

            # Init pygame
            pygame.init()
            win_width=400
            win_height=400
            screen = pygame.display.set_mode((win_width, win_height), DOUBLEBUF)
            pygame.display.set_caption("Crazyflie control")
            screen.fill((50, 55, 60))  # background
            titlefont = pygame.font.SysFont('hack', 20)
            text = titlefont.render('Crazyflie controller', True, (255, 255, 255)); screen.blit(text, (8,10))
            descfont = pygame.font.SysFont('hack', 18)
            text = descfont.render('Keys: w,s,a,d> move;   q,e> turn;   f> stop;   z>land', True, (255, 255, 255)); screen.blit(text, (5, int(win_height/2 - 10)))
            text = descfont.render('g> flatness check and land', True, (255, 255, 255)); screen.blit(text, (5, int(win_height/2 + 10)))
            # text = descfont.render('Press Esc to quit.', True, (255, 255, 255)); screen.blit(text, (5,win_height/2 + 10))
            pygame.display.flip()
            # PyGame loop
            while(1):
                try:
                    # To exit
                    event = pygame.event.poll()
                    # Here, the drone is being controlled manually when battery is not low.
                    # This behaviour can be changed as per desired application
                    if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                        break
                    elif event.type == KEYDOWN and event.key == K_w:
                        mc.stop()
                        mc.start_forward(velocity=forward_vel)
                    elif event.type == KEYDOWN and event.key == K_s:
                        mc.stop()
                        mc.start_back(velocity=forward_vel)
                    elif event.type == KEYDOWN and event.key == K_a:
                        mc.stop()
                        mc.start_left(velocity=forward_vel)
                    elif event.type == KEYDOWN and event.key == K_d:
                        mc.stop()
                        mc.start_right(velocity=forward_vel)
                    elif event.type == KEYDOWN and event.key == K_q:
                        mc.stop()
                        mc.start_turn_left(rate=turn_rate)
                    elif event.type == KEYDOWN and event.key == K_e:
                        mc.stop()
                        mc.start_turn_right(rate=turn_rate)
                    elif event.type == KEYDOWN and event.key == K_f:
                        mc.stop()
                    # elif event.type == KEYDOWN and event.key == K_g:
                    elif vbat < vbat_threhold:  # when battery is low:
                        # Keep moving forward till there's enough light.
                        # This behaviour can be changed to a random walk or anything else as desired
                        while intensity < light_thresh:
                            try:
                                print("Light intensity < threshold")
                                if no obstacle, keep moving forward
                                if(range_left > dist_thresh and
                                   range_front > dist_thresh and
                                   range_right > dist_thresh and
                                   range_back > dist_thresh):
                                mc.start_forward(forward_vel)
                                time.sleep(sleep_time)
                                # Else avoid the obstacle by moving directly away from it.
                                # This behaviour can be changed to turning away, wall-following
                                # or anything else as desired
                                else:
                                    dist_arr = np.array([range_left, range_front,
                                                         range_right, range_back])
                                    smallest_dist = np.argmin(dist_arr)
                                    if smallest_dist == 0:
                                      print('Obstacle to left, moving right....')
                                      mc.start_right(strafe_vel)
                                    elif smallest_dist == 1:
                                      print('Obstacle to front, moving back....')
                                      mc.start_back(strafe_vel)
                                    elif smallest_dist == 2:
                                      print('Obstacle to right, moving left....')
                                      mc.start_left(strafe_vel)
                                    elif smallest_dist == 3:
                                      print('Obstacle to back, moving forward....')
                                      mc.start_forward(forward_vel)
                                    time.sleep(sleep_time)
                            except KeyboardInterrupt:
                                break
                        mc.stop()
                        print("Light intensity > threshold! Checking flatness...")
                        zrange = []
                        flatness = 1  # initialize to some large value
                        flatness_check(mc)
                        # keep checking in different places till a flat landing place is found
                        while flatness > flatness_threshold:
                            try:
                                print("Not flat. Checking flatness at another place...")
                                zrange = []
                                # Move forward by some distance to check for flatness again.
                                # This behaviour can be changed to a random walk or anything else as desired
                                mc.forward(fwd_distance)
                                # Collect time of flight measurements while moving in a square around the area
                                # to be tested for flatness.
                                # This behaviour can be changed to a different trajectory (for eg. a circle) as desired
                                flatness_check(mc)
                            except KeyboardInterrupt:
                                break
                        break
                        elif event.type == KEYDOWN and event.key == K_z:
                            mc.stop()
                            break
                except KeyboardInterrupt:
                    mc.stop()
                    break

            # when all three conditions are satisfied, land
            mc.stop()
            # Stop logging and end
            logconf_pos.stop()
            pos_file_handler.close()
            logconf_range.stop()
            range_file_handler.close()
            logconf_intensity.stop()
            intensity_file_handler.close()
            logconf_vbat.stop()
            vbat_file_handler.close()
            logconf_thrust.stop()
            thrust_file_handler.close()
            mc.land()
