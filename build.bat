call lessc --clean-css static/less/bootstrap.less static/css/bootstrap.min.css
call coffee --compile static/js/
python yaml2json.py "static/data/data-config.yaml" "static/data/data-config.json"