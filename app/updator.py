import os
import argparse
from cnvrgv2 import Cnvrg
import json

cnvrg_workdir = os.environ.get("CNVRG_WORKDIR", "/cnvrg")

project_name = os.environ["CNVRG_PROJECT"]
cnvrg = Cnvrg()
myproj = cnvrg.projects.get(project_name)

def argument_parser():
    parser = argparse.ArgumentParser(description="""Creator""")
    parser.add_argument(
        "--storage_solution",
        action="store",
        dest="storage_solution",
        default="minio",
        required=False,
        help="""type minio or s3""",
    )
    parser.add_argument(
        "--host_address",
        action="store",
        dest="host_address",
        default=False,
        required=False,
        help="""Enter host address of elastic search service""",
    )
    parser.add_argument(
        "--port",
        action="store",
        dest="port",
        default=False,
        required=False,
        help="""Enter port of elastic search service""",
    )
    parser.add_argument(
        "--index",
        action="store",
        dest="index",
        default=False,
        required=False,
        help="""Enter the elastic search index to use""",
    )
    parser.add_argument(
        "--search_field",
        action="store",
        dest="search_field",
        default="content",
        required=False,
        help="""Enter the search field in elastic search index""",
    )
    parser.add_argument(
        "--bucket_name",
        action="store",
        dest="bucket_name",
        default=False,
        required=True,
        help="""Enter the bucket name""",
    )
    parser.add_argument(
        "--api_link",
        action="store",
        dest="api_link",
        default=False,
        required=False,
        help="""Enter the api link""",
    )

    parser.add_argument(
        "--username",
        action="store",
        dest="username",
        default="username",
        required=False,
        help="""Enter the username for ElasticSearch""",
    )

    parser.add_argument(
        "--password",
        action="store",
        dest="password",
        default="password",
        required=False,
        help="""Enter the password for ElasticSearch""",
    )

    parser.add_argument(
        "--queue_url",
        action="store",
        dest="queue_url",
        default="queue_url",
        required=False,
        help="""AWS queue url""",
    )
    
    parser.add_argument(
        "--region_name",
        action="store",
        dest="region_name",
        default="region_name",
        required=False,
        help="""AWS queue url""",
    )    

    parser.add_argument(
        "--scheme",
        action="store",
        dest="scheme",
        default="scheme",
        required=False,
        help="""https/http scheme""",
    )    

    return parser.parse_args()

def main():
    args = argument_parser()
    if 'MINIO_ACCESS_KEY' in os.environ:
        data = {
        **args.__dict__,
        'access_key': os.environ['MINIO_ACCESS_KEY'],
        'secret_key': os.environ['MINIO_SECRET_KEY']
        }
    else:
        data = {
        **args.__dict__,
        'aws_key_id': os.environ['AWS_ACCESS_KEY'],
        'aws_secret_key': os.environ['AWS_SECRET_KEY']
        }
    #save arguments
    with open('commandline_args.txt', 'w') as f:
        json.dump(data, f, indent=2)

    if args.storage_solution.lower() == "minio":
        myproj.put_files(paths=['updator_minio.py','commandline_args.txt','prerun.sh','requirements.txt'])
        w = myproj.webapps.create(
            title="mywebapp",
            image = cnvrg.images.get(name="python", tag="3.8.10"),
            templates=[
                os.environ["CNVRG_COMPUTE_CLUSTER"]
                + "."
                + os.environ["CNVRG_COMPUTE_TEMPLATE"]
            ],
            webapp_type="dash",
            file_name="updator_minio.py",
        )
    elif args.storage_solution.lower() == "s3":
        myproj.put_files(paths=['updator_s3.py','commandline_args.txt','prerun.sh','requirements.txt'])
        w = myproj.webapps.create(
            title="mywebapp",
            image = cnvrg.images.get(name="harindercnvrg/fastrag", tag="latest"),
            templates=[
                os.environ["CNVRG_COMPUTE_CLUSTER"]
                + "."
                + os.environ["CNVRG_COMPUTE_TEMPLATE"]
            ],
            webapp_type="dash",
            file_name="updator_s3.py",
        )
    else:
        assert (
            False
        ), "You need to provide either s3 or minio value for argument storage_solution"


if __name__ == "__main__":
    main()