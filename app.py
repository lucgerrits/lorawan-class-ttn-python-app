import paho.mqtt.client as mqtt
import json
import base64
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from multiprocessing import Process, Value


# to change:
app_id = "luc-test-app-edge"
access_key = ""
mqtt_username = "luc-test-app-edge@ttn"
device_id = "luc-device"

# should stay the same:
mqtt_topic = "v3/" + mqtt_username + "/devices/" + device_id + "/up"
mqtt_address = "eu1.cloud.thethings.network"
mqtt_port = 1883

# Create figure for plotting
fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)
xs = []
ys = []

# The callback for when the client connects to the broker
def on_connect(client, userdata, flags, rc):
    # Print result of connection attempt
    print("Connected with result code {0}".format(str(rc)))
    if (rc != 0):
        print("Error connection.")
        exit(1)
    # Subscribe to the topic, receive any messages published on it
    client.subscribe(mqtt_topic)


def on_message(client, userdata, msg):  # The callback for when a PUBLISH
    global current_value
    # message is received from the server.
    # print("Message received-> " + msg.topic + " " +
    #       str(msg.payload))  # Print a received msg
    json_payload=json.loads(str(msg.payload.decode("utf-8")))
    if "uplink_message" in json_payload:
        if "frm_payload" in json_payload["uplink_message"]:
            raw_payload=json_payload["uplink_message"]["frm_payload"]
            decoded_raw_payload=base64.b64decode(raw_payload)
            print("raw_payload={}".format(raw_payload))
            print("decoded_raw_payload={}".format(decoded_raw_payload))

        if "decoded_payload" in json_payload["uplink_message"]:
            #if autoformat enabled using, typically using cayenne format:
            #See: https://www.thethingsindustries.com/docs/integrations/payload-formatters/cayenne/
            decoded_payload=json_payload["uplink_message"]["decoded_payload"]
            print("decoded_payload={}".format(decoded_payload))
            current_value.value=float(decoded_payload["temperature_1"])
    else:
        print("No payload in message: {}".format(str(msg.payload.decode("utf-8"))))


# This function is called periodically from FuncAnimation
def animate(i, xs, ys, current_value):

    # Add x and y to lists
    xs.append(dt.datetime.now().strftime('%H:%M:%S.%f'))
    ys.append(current_value.value)

    # Limit x and y lists to 20 items
    xs = xs[-20:]
    ys = ys[-20:]

    # Draw x and y lists
    ax.clear()
    ax.plot(xs, ys)

    # Format plot
    plt.xticks(rotation=45, ha='right')
    plt.subplots_adjust(bottom=0.30)
    plt.title('Temperature over Time')
    plt.ylabel('Temperature (deg C)')

def get_current_value():
    global current_value
    print(current_value)
    return current_value

def start_plot(current_value):
    # Set up plot to call animate() function periodically
    ani = animation.FuncAnimation(fig, animate, fargs=(xs, ys, current_value), interval=1000)
    plt.show()



def start_mqtt(current_value):
    # Create instance of client with client ID
    client = mqtt.Client("my_mqtt_instance")
    client.on_connect = on_connect  # Define callback function for successful connection
    client.on_message = on_message  # Define callback function for receipt of a message
    # client.connect("m2m.eclipse.org", 1883, 60)  # Connect to (broker, port, keepalive-time)
    client.username_pw_set(mqtt_username, access_key)
    client.connect(mqtt_address, mqtt_port)
    client.loop_forever()  # Start networking daemon

if __name__ == '__main__':
    current_value = Value('d', 0.0)
    p_start_plot = Process(name='p_start_plot', target=start_plot, args=(current_value,))
    p_start_mqtt = Process(name='p_start_mqtt', target=start_mqtt, args=(current_value,))
    p_start_plot.start()
    p_start_mqtt.start()
    p_start_plot.join()
    p_start_mqtt.join()