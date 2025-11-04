import json, time
import paho.mqtt.client as paho
from paho import mqtt
from dotenv import load_dotenv

load_dotenv()
from mqtt_config import *
import helper_functions as hf

def on_publish(client, userdata, mid, properties=None, reasonCode=None):
    print(f"Message {mid} acknowledged by broker")


# Set up MQTT publisher
client = paho.Client(client_id="mac-orchestrator", protocol=paho.MQTTv5)
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
client.on_publish = on_publish

print(f"Connecting to {MQTT_BROKER}:{MQTT_PORT}")
client.connect(MQTT_BROKER, int(MQTT_PORT))
topic = "lab/experiments/new"

client.loop_start()

n = 3 #number of iterations
for i in range(n):
    print(f"Current Iteration is {i}")
    list_of_drugs = (['IBP']  + ['LOV']  + ['DCF']  + ['GLV']) * 2
    print(f"List of drugs are {list_of_drugs}")

    # Generate recommendations
    time_start = time.time()
    df_design, ax_client, data_so_far, best_concs = hf.run_optimizer(current_iteration=i, drug_list= list_of_drugs, bopt=0)
    time_end = time.time()
    time_duration = round((time_end - time_start)/60,2)

    print("Time taken for optimization: " + str(time_duration) + " mins")
    print("Time taken for optimization: " + str(time_duration * 60) + " seconds")

    # process results
    ax_client = hf.load_design_optimizer(n)
    ax_client.get_trials_data_frame()
    df_design, df_vol = hf.design_to_vol (n)
    df_design['constraint'] = df_design['drug_name'].map(best_concs).fillna(0.0)


    # TODO: How to get rid of these inputs
    plate_well = input("Enter the plate well starting well (e.g., F1): ")
    deepplate_well = input("Enter the deep plate well starting well (e.g., F1): ")

    print("Wellplate will start at: " + plate_well)
    print("Deep plate will start at: " + deepplate_well)

    payload = {
        "iteration": i,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metadata": {
            "plate_well": plate_well,
            "deepplate_well": deepplate_well
        },
        "experiments": df_vol.to_dict(orient="records")
    }

    info = client.publish(topic, json.dumps(payload), qos=1, retain=True)
    info.wait_for_publish(timeout=5)
    print("publish rc =", info.rc, "mid =", info.mid, "is_published =", info.is_published())

client.loop_stop()
client.disconnect()
