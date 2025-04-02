const express = require('express');
const router = express.Router();
const Player = require('../models/player');
const Match = require('../models/match');
const mongoose = require('mongoose');

// Get all departments
router.get('/departments', async (req, res) => {
    try {
        const departments = await Player.distinct("Department");
        res.json(departments);
    } catch (err) {
        console.error('Department fetch error:', err);
        res.status(500).json({ 
            message: 'Failed to fetch departments',
            error: err.message 
        });
    }
});

// Get players by department
router.get('/players/:department', async (req, res) => {
    try {
        const department = req.params.department.trim();
        const players = await Player.find({
            Department: new RegExp(`^${department}$`, 'i'),
            Status: 'Active'
        }).select('Name Role _id');

        if (players.length === 0) {
            return res.status(404).json({ 
                message: "No active players found for this department" 
            });
        }
        
        res.json(players);
    } catch (err) {
        console.error('Player fetch error:', err);
        res.status(500).json({ 
            message: 'Server error while fetching players',
            error: err.message 
        });
    }
});

// Submit teams
router.post('/team', async (req, res) => {
    try {
        const { teamA, teamB } = req.body;
        
        // Validate request structure
        if (!teamA || !teamB) {
            return res.status(400).json({ message: "Both teams are required" });
        }

        // Validate team structure
        const validateTeam = (team) => {
            if (!team.department || !team.players) return false;
            if (!Array.isArray(team.players)) return false;
            if (team.players.length !== 11) return false;
            return team.players.every(id => mongoose.Types.ObjectId.isValid(id));
        };

        if (!validateTeam(teamA) || !validateTeam(teamB)) {
            return res.status(400).json({ 
                message: "Invalid team structure. Each team must have a department and 11 valid player IDs" 
            });
        }

        // Check department existence
        const departmentsExist = await Player.distinct('Department', {
            Department: { $in: [teamA.department, teamB.department] }
        });
        
        if (departmentsExist.length !== 2) {
            return res.status(400).json({ 
                message: "One or both departments are invalid" 
            });
        }

        // Create and save match
        const newMatch = new Match({
            teamA: {
                department: teamA.department,
                players: teamA.players.map(id => new mongoose.Types.ObjectId(id))
            },
            teamB: {
                department: teamB.department,
                players: teamB.players.map(id => new mongoose.Types.ObjectId(id))
            }
        });

        await newMatch.save();

        res.json({
            success: true,
            message: 'Teams submitted successfully!',
            matchId: newMatch._id,
            teamA: teamA.department,
            teamB: teamB.department
        });

    } catch (err) {
        console.error('Team submission error:', err);
        res.status(500).json({ 
            success: false,
            message: 'Failed to save teams',
            error: err.message 
        });
    }
});

module.exports = router;