FROM python:3.6

RUN pip --no-cache-dir install \
    backtrader\
    boto3 \
    pandas

RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && unzip awscliv2.zip && ./aws/install && rm awscliv2.zip && rm -rf aws/

ENV ENVIRONMENT="/home/environment"
RUN mkdir -p $ENVIRONMENT/input
RUN mkdir -p $ENVIRONMENT/output
COPY backtest.py $ENVIRONMENT/
CMD aws s3 cp s3://$BUCKET/$PREFIX/trial_$TRIAL/input/ $ENVIRONMENT/input/ --recursive && \
    aws s3 cp s3://$BUCKET/$PREFIX/data.csv $ENVIRONMENT/data.csv && \
    python $ENVIRONMENT/backtest.py && \
    aws s3 cp $ENVIRONMENT/output/ s3://$BUCKET/$PREFIX/trial_$TRIAL/output/ --recursive
