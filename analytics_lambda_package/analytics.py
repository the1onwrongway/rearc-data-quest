import json
import boto3
import math


s3 = boto3.client("s3")


def lambda_handler(event,context):
    print('Received SQS Event')

    for record in event["Records"]:
        #body = json.loads(record["body"])
        #s3_event = body["Records"][0]

        body = json.loads(record["body"])

        # Ignore S3 test events
        if body.get("Event") == "s3:TestEvent":
            print("Ignoring S3 TestEvent")
            return

        s3_event = body["Records"][0]
         
        bucket = s3_event["s3"]["bucket"]["name"]
        key =  s3_event["s3"]["object"]["key"]

        print(f"Processing population file :s3://{bucket}/{key}")


        #------------------------
        # 1. Load Population JSON
        #------------------------

        response = s3.get_object(Bucket = bucket, Key = key)
        population_json = json.loads(response["Body"].read())

        population_data = population_json["data"]

        #Filter years 2013-2018
        pop_filtered = [
            row for row in population_data
            if 2013 <= int(row["Year"]) <= 2018
        ]

        populations = [float(row["Population"]) for row in pop_filtered]

        mean_population = sum(populations)/ len(populations)

        variance = sum((x-mean_population)**2 for x in populations) / len(populations)

        std_population = math.sqrt(variance)

        print('Population Stats (2013-2018)')
        print("Mean: ", mean_population)
        print("Std Dev: ", std_population)

        #------------------------
        # 2. Load BLS Data
        #------------------------

        bls_key = "raw/bls/pr.data.0.Current"

        bls_response = s3.get_object(Bucket=bucket, Key=bls_key)
        bls_content = bls_response["Body"].read().decode("utf-8").splitlines()


        header = bls_content[0].split("\t")
        header = [h.strip() for h in header]

        rows = []
        for line in bls_content[1:]:
            parts = line.split("\t")
            parts = [p.strip() for p in parts]
            if len(parts) >= 4:
                rows.append(dict(zip(header,parts)))

        #---------------------------
        # 3. Best Year Per series_id
        #---------------------------

        yearly_totals = {}

        for row in rows:
            series = row["series_id"]
            year = row["year"]
            value = float(row["value"])

            yearly_totals.setdefault(series,{})
            yearly_totals[series].setdefault(year,0)
            yearly_totals[series][year] += value

        best_years = {}

        for series,years in yearly_totals.items():
            best_year = max(years, key=years.get)
            best_years[series] = (best_year,years[best_year])

        print('Sample Best Year Output:')
        for i, (series,(year, value)) in enumerate(best_years.items()):
            if i>=5:
                break
            print(series,year,value)


        #---------------------------
        # 4. Target Join
        #---------------------------

        target_series = "PRS30006032"
        target_period = "Q01"


        target_rows = [
            row for row in rows
            if row["series_id"] == target_series
            and row["period"] == target_period
        ]

        print("Target Join Output:")
        for row in target_rows:
            year = int(row["year"])
            population_match = next(
                (r["Population"] for r in population_data if int(r["Year"])==year),
                 None
                 )
            
            print(
                target_series,
                year,
                target_period,
                row["value"],
                population_match
            )
            
    return{
        "statusCode": 200,
        "body":"Analytics completed"
    }