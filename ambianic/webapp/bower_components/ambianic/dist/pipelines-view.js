// Create a Paper.js Path to draw a line into it:
var line = new Path();
// Give the stroke a color
line.strokeColor = 'black';
var start = new Point(100, 100);
// Move to start and draw a line from there
line.moveTo(start);
// Note the plus operator on Point objects.
// PaperScript does that for us, and much more!
line.lineTo(start + [ 100, -50 ]);

// Create a circle shaped path with its center at the center
// of the view and a radius of 30:
var circle = new Path.Circle({
	center: view.center,
	radius: 30,
	strokeColor: 'red'
});

circle.moveTo(view.center)

// Create a raster item using the image tag with id='mona'
var raster = new Raster('img');

// Move the raster to the center of the view
raster.position = view.center;

// Scale the raster by 50%
raster.scale(0.5);

// Rotate the raster by 45 degrees:
raster.rotate(45);


var circle = new Path.Circle({
	center: [80, 50],
	radius: 5,
	fillColor: 'red'
});

// Create a rasterized version of the path:
var raster = circle.rasterize();

// Move it 100pt to the right:
raster.position.x += 100;

// Scale the path and the raster by 300%, so we can compare them:
circle.scale(5);
raster.scale(5);


function onResize(event) {
	// Whenever the window is resized, recenter the path:
	// circle.position = view.center;
	// raster.position = view.center;
}
