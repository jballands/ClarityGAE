var xs = [1,    1/2,      -1/2,     -1,   -1/2,      1/2]
var ys = [0,    0.866,    0.866,    0,    -0.866,    -0.866]
var loader = new Sonic({
    'width': 128,
    'height': 128,
    'fillColor': '#0091f6',
    'fps': 100,
    'trailLength': 0.75,
    'path': [
        ['line', 104.0, 64.0, 84.0, 98.6],
        ['line', 84.0, 98.6, 44.0, 98.6],
        ['line', 44.0, 98.6, 24.0, 64.0],
        ['line', 24.0, 64.0, 44.0, 29.4],
        ['line', 44.0, 29.4, 84.0, 29.4],
        ['line', 84.0, 29.4, 104.0, 64.0]
    ],
    'step': function(point, index) {
        
        this._.beginPath();
        this._.moveTo(point.x, point.y);
        this._.arc(point.x, point.y, index * 3.5, 0, Math.PI*2, false);
        this._.closePath();
        this._.fill();

    }