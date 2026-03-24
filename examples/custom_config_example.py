
import json
import babyros
import time

if __name__ == "__main__":
    # Ensure BabyROS is configured before creating any nodes
    babyros.configure(connect_endpoints=["tcp/localhost:7447"])

    # The session is created automatically inside the Publisher
    imu_pub = babyros.node.Publisher(topic="imu")
    print("Created publisher!")

    # Test endpoint of Session Manager config
    config = babyros.node.SessionManager.get_session_config()
    config_dict = json.loads(str(config))
    print("SessionManager test endpoint: ", config_dict["connect"]["endpoints"])

    try:
        while True:
            # Publish some dummy IMU data
            data = {"accel": [0.0, 0.0, 0.0], "gyro": [0.0, 0.0, 0.0]}
            imu_pub.publish(data)
            print(f"Published IMU data: {data}")
            time.sleep(0.5)  # Publish at 1 Hz

    except KeyboardInterrupt:
        print("Publishing interrupted")
    finally:
        imu_pub.delete()
        babyros.node.SessionManager.delete()