import carla
import time
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1', help='CARLA Server IP')
    parser.add_argument('--port', default=2000, type=int, help='CARLA Server Port')
    parser.add_argument('--log_name', default='simulation_snapshot.log', help='Name of the CARLA log file')
    args = parser.parse_args()

    # Connect to CARLA
    print(f"Connecting to CARLA at {args.host}:{args.port}...")
    client = carla.Client(args.host, args.port)
    client.set_timeout(10.0)

    # Start the built-in CARLA recorder
    print(f"Starting CARLA Recorder. Saving to: {args.log_name}")
    client.start_recorder(args.log_name)

    try:
        print("Simulation is running and recording. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping CARLA Recorder...")
        client.stop_recorder()

if __name__ == '__main__':
    main()