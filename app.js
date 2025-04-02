const cors = require('cors');
const express = require('express');
const mongoose = require('mongoose');
const path = require('path');
const connectDB = require('./config/db');

const app = express();

// Connect Database
connectDB();

// Middleware
app.use(cors({
  origin: 'http://localhost:3001',
  methods: ['GET', 'POST'],
  allowedHeaders: ['Content-Type']
}));

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Routes
app.use('/api', require('./routes/api'));

// Views (only if you're using EJS for server-side rendering)
app.set('view engine', 'ejs');
app.use(express.static('public'));
app.get('/', (req, res) => res.render('index'));
const PORT = process.env.PORT || 3002; // Use a different port
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));