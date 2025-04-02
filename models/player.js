const mongoose = require('mongoose');

const playerSchema = new mongoose.Schema({
    Player_ID: String,
    Name: String,
    Role: String,
    Department: String,
    Year_of_Study: Number,
    Status: String,
    Matches_Played: Number,
    Runs_Scored: Number,
    Batting_Average: Number,
    Strike_Rate: Number,
    Wickets_Taken: Number,
    Economy_Rate: Number
}, { collection: 'Player_per' });

// models/player.js - Add collection name
module.exports = mongoose.model('Player', playerSchema);
//                                                     
