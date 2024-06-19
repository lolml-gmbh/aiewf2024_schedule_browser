FROM mambaorg/micromamba:latest
USER root
RUN mkdir /app
ADD *.txt run_app.sh *.py *.png /app/

USER $MAMBA_USER
RUN micromamba install -y -n base -c conda-forge -c pytorch --channel-priority strict --file \
    /app/conda_packages.txt && micromamba clean --all --yes

# ARG MAMBA_DOCKERFILE_ACTIVATE=1
# RUN pip install -r /app/pip_packages.txt --upgrade --no-cache-dir

EXPOSE 8080
ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "/app/run_app.sh"]
