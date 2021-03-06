function parseFreeRooms(callback) {
	$.getJSON('rooms/free', function(json) {
		parseFree(json, callback);
	}).fail(function() {
		console.log("ERROR");
	});
}

function parseFree(json, callback) {
	var hashOfFree = {};
	for (var i = 0; i < json.rooms.length; i++) {
		var singleJson = json.rooms[i];
		var id = singleJson["aux_id"];
		var name = singleJson["name"];
		var floor = singleJson["floor"];
		hashOfFree[id] = [name, floor];
	}
	callback(hashOfFree);
}
