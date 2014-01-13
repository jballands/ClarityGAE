call lessc --clean-css static/less/bootstrap.less static/css/bootstrap.min.css
python yaml2json.py "static/data/data-config.yaml" "static/data/data-config.json"