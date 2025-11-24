from dagster import DynamicPartitionsDefinition

# Define the dynamic partition for stations
# This is shared between the sensor (definitions.py) and the assets (ingestion.py)
knmi_stations_def = DynamicPartitionsDefinition(name="knmi_stations")
