const mongoose = require('mongoose');

const matchSchema = new mongoose.Schema({
    teamA: {
        department: { type: String, required: true },
        players: [{ 
            type: mongoose.Schema.Types.ObjectId,
            ref: 'Player',
            required: true
        }]
    },
    teamB: {
        department: { type: String, required: true },
        players: [{ 
            type: mongoose.Schema.Types.ObjectId,
            ref: 'Player',
            required: true
        }]
    },
    date: { 
        type: Date, 
        default: Date.now 
    }
});

module.exports = mongoose.model('Match', matchSchema);