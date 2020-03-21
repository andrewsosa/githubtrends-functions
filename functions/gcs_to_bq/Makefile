.PHONY: deploy

deploy:
	gcloud functions deploy gcs_to_bq \
		--runtime python37 \
		--trigger-resource ghtrends \
		--trigger-event google.storage.object.finalize

test:
	PYTHONPATH=$(shell pwd) pytest tests/
