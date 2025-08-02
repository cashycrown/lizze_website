//Hook up the tweet display

$(document).ready(function() {
	   
	$(".countdown").countdown({
				date: "13 august 2025 18:30:00",
				format: "on"
			},
			
			function() {
				// callback function
			});

});	