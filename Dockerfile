FROM python:2-onbuild
CMD [ "chalice", "deploy", "--no-autogen-policy" ]
