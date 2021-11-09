# IoTSSC_app

This Django application was built to receive activity tracker data from an embedded device, using MQTT messages pushed by Google Cloud. Incoming sensor readings are classified into running/walking/no activity using a pre-trained model. Classified activities are stored in a database, keeping track of individual activities and their duration.
The application can be polled for live and historical data.
Daily milestones for walking and running are pushed to Android devices using Firebase notifications.
