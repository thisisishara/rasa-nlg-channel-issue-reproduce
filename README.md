# rasa_nlg_channel_issue_reproduce
Exact steps to reproduce Rasa open source channel name retrieval issue in the example sanic-based NLG server provided

```json
{
    "developer": "thisisishara",
    "python_version": "3.10.10",
    "environment": "conda",
    "rasa_version": "3.6.0",
    "rasa_oss_issue_url": "https://rasa-open-source.atlassian.net/browse/OSS-714",
    "pr_url": "in_progress"
}
```

## Issue description
When using `custom channels` and `channel-specific response variations` with Rasa Open Source, using the given `nlg_server.py` script in the official Rasa codebase is not able to extract and return the correct response variation according to the latest input channel.

This is due to a bug introduced by the given nlg server script, which does not correctly extract the name of the channel.
<hr>

## Steps to reproduce
You can use the given rasa bot and nlg server scripts to reproduce the issue easily. 

- Setup a python 3.9 or 3.10 conda or venv environment and then install the given dependencies by running the following command.
```shell
cd {path_to_cloned_repo}/bot
pip install -r requirements.txt
```

- First of all, train the given bot by running
```shell
rasa train
```

- Run the rasa server with custom connectors by executing the following command in the terminal
```shell
rasa run --enable-api --cors "*"
```

- To reproduce the default nlg behaviour/bug, run the official NLG server available in the Rasa repository, in a separate terminal instance. DO NOT forget to attach the domain file via the -d argument.
```shell
cd {path_to_cloned_repo}/nlg
python nlg_server.py -d ../bot/domain.yml
```

- Open up a API testing utility such as postman, or simply use a different python script to send a POST request to the rasa server. The request should look like this if you're using python.
```python
import requests
import json

url = "http://localhost:5005/webhooks/myio2/webhook"

payload = json.dumps({
  "sender": "default",
  "message": "hi"
})
headers = {
  'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)

```
- or it should look like this if using `curl`.
```shell
curl --location 'http://localhost:5005/webhooks/myio2/webhook' \
--header 'Content-Type: application/json' \
--data '{
    "sender": "default",
    "message": "hi"
}'
```
⚠ Note that the channel is `myio2` custom connector and the message intent is `greet`. However, notice that the output generated by the NLG is not the correct response variant.

domain.yml:
```yml
responses:
  utter_greet:
  - text: "Hey! How are you?"
  - text: "Hey from custom channel"
    channel: myio
  - text: "Hi from custom channel 2"
    channel: myio2
```
NLG response:
```json
[
    {
        "recipient_id": "default",
        "text": "Hey! How are you?"
    }
]
```

- `nlg_server_fixed.py` fixes this issue by correctly extracting the name of the custom input channel. To test this, take down the `nlg_server.py` and run the `nlg_server_fixed.py` by executing the following command in the NLG terminal.
```shell
# Ctrl + C to stop the running NLG server
cd {path_to_cloned_repo}/nlg
python nlg_server_fixed.py -d ../bot/domain.yml
```

- Send another POST request with the same body as in previous request.
```shell
curl --location 'http://localhost:5005/webhooks/myio/webhook' \
--header 'Content-Type: application/json' \
--data '{
    "sender": "default",
    "message": "hi"
}'
```
- Notice that this time, the correct response is generated by the external NLG server. Compare it with the domain of the bot to verify the claim.

NLG response:
```json
[
    {
        "recipient_id": "default",
        "text": "Hi from custom channel 2"
    }
]
```

<hr>