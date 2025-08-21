<?php
/**
 * Plugin de Dados de Diplomas para Moodle
 * 
 * Este plugin fornece uma API para o sistema de automatização de diplomas
 * obter dados dos estudantes de forma segura e estruturada.
 * 
 * @package    local_diploma_data
 * @copyright  2025 Carlos Antonio de Oliveira Piquet
 * @author     Carlos Antonio de Oliveira Piquet <carlospiquet.projetos@gmail.com>
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

defined('MOODLE_INTERNAL') || die();

$plugin->component = 'local_diploma_data';
$plugin->version   = 2025082000;  // YYYYMMDDXX
$plugin->requires  = 2021051700;  // Moodle 4.0+
$plugin->maturity  = 200;  // MATURITY_STABLE
$plugin->release   = 'v1.0.0';
$plugin->dependencies = array();

// Informações adicionais do plugin
$plugin->description = 'Plugin para integração com sistema automatizador de diplomas desenvolvido por Carlos Antonio de Oliveira Piquet';
$plugin->author = 'Carlos Antonio de Oliveira Piquet (carlospiquet.projetos@gmail.com)';
$plugin->archivefile = 'diploma_data.zip';
