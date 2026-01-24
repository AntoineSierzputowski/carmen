-- Script SQL pour initialiser la base de données Carmen
-- Exécutez ce script avec: mysql -u root -p < init_database.sql

-- Créer la base de données si elle n'existe pas
CREATE DATABASE IF NOT EXISTS carmen CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Utiliser la base de données
USE carmen;

-- Note: Les tables seront créées automatiquement par SQLAlchemy lors du premier démarrage
-- Ce script crée uniquement la base de données
