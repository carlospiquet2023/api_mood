<?php
/**
 * Definição de serviços web para o plugin diploma_data
 * 
 * Este arquivo define as funções que estarão disponíveis via API
 * para o sistema de automatização de diplomas.
 * 
 * @package    local_diploma_data
 * @copyright  2025 Carlos Antonio de Oliveira Piquet
 * @author     Carlos Antonio de Oliveira Piquet <carlospiquet.projetos@gmail.com>
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

defined('MOODLE_INTERNAL') || die();

// Definição das funções disponíveis via webservice
$functions = array(
    
    // Função principal para obter dados completos do estudante
    'local_diploma_data_get_user_diploma_details' => array(
        'classname'   => 'local_diploma_data_external',
        'methodname'  => 'get_user_diploma_details',
        'classpath'   => 'local/diploma_data/classes/external.php',
        'description' => 'Obtém dados completos do utilizador e curso para geração de diplomas com QR codes.',
        'type'        => 'read',
        'capabilities' => 'moodle/user:viewdetails',
        'services'    => array(),
    ),
    
    // Função para buscar utilizadores por nome ou email
    'local_diploma_data_search_users' => array(
        'classname'   => 'local_diploma_data_external',
        'methodname'  => 'search_users',
        'classpath'   => 'local/diploma_data/classes/external.php',
        'description' => 'Busca utilizadores por nome ou email.',
        'type'        => 'read',
        'capabilities' => 'moodle/user:viewdetails',
        'services'    => array(),
    ),
    
    // Função para verificar conclusão de curso
    'local_diploma_data_verify_course_completion' => array(
        'classname'   => 'local_diploma_data_external',
        'methodname'  => 'verify_course_completion',
        'classpath'   => 'local/diploma_data/classes/external.php',
        'description' => 'Verifica se um utilizador completou um curso específico.',
        'type'        => 'read',
        'capabilities' => 'moodle/course:view',
        'services'    => array(),
    ),

    // Função para verificar diploma por QR code
    'local_diploma_data_verify_diploma_qr' => array(
        'classname'   => 'local_diploma_data_external',
        'methodname'  => 'verify_diploma_qr',
        'classpath'   => 'local/diploma_data/classes/external.php',
        'description' => 'Verifica a autenticidade de um diploma a partir de dados de QR Code.',
        'type'        => 'read',
        'capabilities' => '', // Acesso público
        'services'    => array(),
    )
);

// Serviços personalizados (opcional)
$services = array(
    'Sistema de Diplomas' => array(
        'functions' => array(
            'local_diploma_data_get_user_diploma_details',
            'local_diploma_data_search_users',
            'local_diploma_data_verify_course_completion',
            'local_diploma_data_verify_diploma_qr'
        ),
        'restrictedusers' => 0,
        'enabled' => 1,
        'shortname' => 'diploma_system',
        'downloadfiles' => 0,
        'uploadfiles' => 0
    )
);
