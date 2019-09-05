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
	strokeColor: 'black'
});

circle.moveTo(view.center)

function onResize(event) {
	// Whenever the window is resized, recenter the path:
	circle.position = view.center;
}