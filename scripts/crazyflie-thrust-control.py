import argparse
import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
import logging
import os
import time


hover_thrust = []

# TODO: add these to argparse
takeoff_height = 0.3        # m
forward_vel = 0.1           # m/s
turn_rate = 360.0 / 10.0    # rot/s

## Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)


def log_vbat_callback(timestamp, data, logconf):
    '''
    Logging callback function for battery voltage
    '''
    print("timestamp={}, vbat={} V".format(timestamp, data['pm.vbat']))
    if args.write_to_file:
        vbat_file_handler.write("{},{}\n".format(timestamp, data['pm.vbat']))


def log_thrust_callback(timestamp, data, logconf):
    '''
    Logging callback function for battery voltage
    '''
    global hover_thrust
    hover_thrust.append(data['stabilizer.thrust'])


def spin():
    '''
    Keep script alive until KeyboardInterrupt is received
    '''
    while(1):
        try:
            time.sleep(0.01)
        except KeyboardInterrupt:
            break


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Script to control the crazyflie\'s thrust')
    parser.add_argument('-t', '--thrust', type=int, help='Manually commanded thrust (in percentage). Use 20%% to 100%%')
    parser.add_argument('-ht', '--hover', action='store_true', help='Hover thrust')
    parser.add_argument('-u', '--uri', type=str, default='69', help='URI of the crazyflie to connect to')
    parser.add_argument('-v', '--log_vbat', action='store_true', default=False, help='Log battery voltage')
    parser.add_argument('-w', '--write_to_file', action='store_true', default=False, help='Write logging variables to file')
    parser.add_argument('-n', '--trial_no', type=int, help='Trial number (for saving vbat information to file)')
    args = parser.parse_args()

    # Argument list sanity checks
    if args.write_to_file and not args.log_vbat:
        parser.error('Cannot write vbat to file without logging. Pass -v along with -w.')

    if args.thrust is not None and args.hover:
        parser.error('Only pass one of -t or -ht')

    if (args.thrust is None == args.hover) and args.trial_no is not None:
        parser.error('Pass the -n option with either -t or -ht')

    # Initialize drivers for communication using CRTP
    cflib.crtp.init_drivers(enable_debug_driver=False)

    # Connect to the crazyflie
    cf = Crazyflie(rw_cache=os.path.expanduser("~") + "/.cache")
    cf.open_link('radio://0/' + args.uri + '/2M/E7E7E7E7E7')
    time.sleep(5)  # give some time to establish connection; 5 sec seems to work
    print('radio://0/' + args.uri + '/2M/E7E7E7E7E7' + " connected?: " + str(cf.is_connected()))

    # Logging battery voltage
    if args.log_vbat:
        # Overwrite logfile contents
        if args.write_to_file:
            # Unless trial no is specified, default to default filename
            if args.trial_no is None:
                filename = "vbat.csv"
            # Else choose appropirate filename
            else:
                if args.hover:
                    filename = "vbat_h_n-" + str(args.trial_no) + ".csv"
                else:
                    filename = "vbat_t-" + str(args.thrust) + "_n-" + str(args.trial_no) + ".csv"
            vbat_file_handler = open("../data/" + filename, "w")
            vbat_file_handler.close()
            vbat_file_handler = open("../data/" + filename, "a")
        logconf_vbat = LogConfig(name="Battery voltage", period_in_ms=1000)
        logconf_vbat.add_variable('pm.vbat', 'float')
        cf.log.add_config(logconf_vbat)
        logconf_vbat.data_received_cb.add_callback(log_vbat_callback)

    if args.thrust is not None:
        # Send thrust=0 first so that the crazyflie-firmware's safety protection requirements are met
        cf.commander.send_setpoint(0.0, 0.0, 0, 0)
        time.sleep(0.1)

        # Using param framework for low-level motor speed control
        print("Sending thrust " + str(args.thrust) + "% to " + 'radio://0/' + args.uri + '/2M/E7E7E7E7E7' + " ...")
        cf.param.set_value("motorPowerSet.m1", int(args.thrust * ((2**16)-1)/100)); time.sleep(0.01)
        cf.param.set_value("motorPowerSet.m2", int(args.thrust * ((2**16)-1)/100)); time.sleep(0.01)
        cf.param.set_value("motorPowerSet.m3", int(args.thrust * ((2**16)-1)/100)); time.sleep(0.01)
        cf.param.set_value("motorPowerSet.m4", int(args.thrust * ((2**16)-1)/100)); time.sleep(0.01)
        cf.param.set_value("motorPowerSet.enable", 1)
        
        time.sleep(3)  # wait for some time before starting logging battery voltage
        if args.log_vbat:
            logconf_vbat.start()  # start logging battery voltage

        spin()

        # Turn off motors
        print("Turning off motors and closing connection with " + 'radio://0/' + args.uri + '/2M/E7E7E7E7E7' + " ...")
        cf.param.set_value("motorPowerSet.m1", 0); time.sleep(0.01)
        cf.param.set_value("motorPowerSet.m2", 0); time.sleep(0.01)
        cf.param.set_value("motorPowerSet.m3", 0); time.sleep(0.01)
        cf.param.set_value("motorPowerSet.m4", 0); time.sleep(0.01)
        cf.param.set_value("motorPowerSet.enable", 0)

    # Hover at hover thrust
    elif args.hover:
        # This part gets rid of the 'Hello from PyGame...' message
        from os import environ
        environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
        import pygame
        from pygame.locals import *
        from cflib.positioning.motion_commander import MotionCommander
        logconf_thrust = LogConfig(name="Thrust", period_in_ms=1000)
        logconf_thrust.add_variable('stabilizer.thrust', 'float')
        cf.log.add_config(logconf_thrust)
        logconf_thrust.data_received_cb.add_callback(log_thrust_callback)
        with MotionCommander(cf, default_height=takeoff_height) as mc:
            print("Take off " + 'radio://0/' + args.uri + '/2M/E7E7E7E7E7' + " at hover thrust.")
            mc.stop()
            time.sleep(3)  # give some time to take off before starting logging battery voltage
            logconf_vbat.start()  # start logging battery voltage
            logconf_thrust.start()  # start logging thrust

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
            #text = descfont.render('Press Esc to quit.', True, (255, 255, 255)); screen.blit(text, (5,win_height/2 + 10))
            pygame.display.flip()
            # PyGame loop
            while(1):
                try:
                    # To exit
                    event = pygame.event.poll()
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
                    elif event.type == KEYDOWN and event.key == K_z:
                        mc.stop()
                        logconf_vbat.stop()
                        break
                except KeyboardInterrupt:
                    break

            logconf_thrust.stop()
            mc.land()
            print('radio://0/' + args.uri + '/2M/E7E7E7E7E7' + " landed.")
            print("Stopped logging thrust.")
            print("Average hover thrust for the flight was: {} %".format(sum(hover_thrust)*100/len(hover_thrust)/((2**16)-1)))
    else:
        spin()

    # Stop logging battery voltage
    if args.log_vbat:
        logconf_vbat.stop()
        print("Stopped logging vbat.")
        if args.write_to_file:
            vbat_file_handler.close()
            print("Closed the csv file.")

    # Disconnect and end
    cf.close_link()
    print("Exiting...")
