<?php
// This file is part of Moodle - http://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Moodle is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Moodle.  If not, see <http://www.gnu.org/licenses/>.

/**
 * Diploma Data API Functions
 *
 * @package    local_diploma_data
 * @copyright  2025 Sistema de Diplomas
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

defined('MOODLE_INTERNAL') || die();

/**
 * Busca dados de estudante por nome
 *
 * @param string $student_name Nome do estudante
 * @return array Dados do estudante
 */
function diploma_data_get_student_data($student_name) {
    global $DB;

    try {
        // Buscar usuários por nome
        $sql = "SELECT id, firstname, lastname, email, username 
                FROM {user} 
                WHERE deleted = 0 
                AND CONCAT(firstname, ' ', lastname) LIKE ?
                ORDER BY firstname, lastname 
                LIMIT 10";

        $search_term = '%' . $DB->sql_like_escape($student_name) . '%';
        $users = $DB->get_records_sql($sql, array($search_term));

        $results = array();
        foreach ($users as $user) {
            $results[] = array(
                'id' => $user->id,
                'firstname' => $user->firstname,
                'lastname' => $user->lastname,
                'fullname' => $user->firstname . ' ' . $user->lastname,
                'email' => $user->email,
                'username' => $user->username
            );
        }

        return array(
            'success' => true,
            'students' => $results,
            'total' => count($results)
        );

    } catch (Exception $e) {
        return array(
            'success' => false,
            'error' => $e->getMessage(),
            'students' => array(),
            'total' => 0
        );
    }
}

/**
 * Obtém dados de conclusão de curso
 *
 * @param int $user_id ID do usuário
 * @param int $course_id ID do curso (opcional)
 * @return array Dados de conclusão
 */
function diploma_data_get_course_completion($user_id, $course_id = 0) {
    global $DB;

    try {
        $sql = "SELECT cc.id, cc.userid, cc.course, cc.timeenrolled, cc.timestarted, cc.timecompleted,
                       c.fullname as coursename, c.shortname, c.category,
                       u.firstname, u.lastname
                FROM {course_completions} cc
                JOIN {course} c ON c.id = cc.course
                JOIN {user} u ON u.id = cc.userid
                WHERE cc.userid = ?";

        $params = array($user_id);

        if ($course_id > 0) {
            $sql .= " AND cc.course = ?";
            $params[] = $course_id;
        }

        $sql .= " ORDER BY cc.timecompleted DESC";

        $completions = $DB->get_records_sql($sql, $params);

        $results = array();
        foreach ($completions as $completion) {
            $results[] = array(
                'course_id' => $completion->course,
                'course_name' => $completion->coursename,
                'course_shortname' => $completion->shortname,
                'time_enrolled' => $completion->timeenrolled,
                'time_started' => $completion->timestarted,
                'time_completed' => $completion->timecompleted,
                'completion_date' => $completion->timecompleted ? 
                    date('Y-m-d H:i:s', $completion->timecompleted) : null,
                'student_name' => $completion->firstname . ' ' . $completion->lastname
            );
        }

        return array(
            'success' => true,
            'completions' => $results,
            'total' => count($results)
        );

    } catch (Exception $e) {
        return array(
            'success' => false,
            'error' => $e->getMessage(),
            'completions' => array(),
            'total' => 0
        );
    }
}

/**
 * Verifica a autenticidade de um diploma via QR Code
 *
 * @param string $qr_data Dados do QR Code
 * @return array Resultado da verificação
 */
function diploma_data_verify_diploma($qr_data) {
    global $DB;

    try {
        // Decodificar dados do QR (assumindo JSON)
        $diploma_data = json_decode($qr_data, true);
        
        if (!$diploma_data) {
            return array(
                'valid' => false,
                'error' => 'Dados do QR Code inválidos'
            );
        }

        // Verificar campos obrigatórios
        $required_fields = array('student_id', 'course_id', 'completion_date');
        foreach ($required_fields as $field) {
            if (!isset($diploma_data[$field])) {
                return array(
                    'valid' => false,
                    'error' => "Campo obrigatório ausente: $field"
                );
            }
        }

        // Verificar se o estudante existe
        $user = $DB->get_record('user', array('id' => $diploma_data['student_id']));
        if (!$user) {
            return array(
                'valid' => false,
                'error' => 'Estudante não encontrado'
            );
        }

        // Verificar conclusão do curso
        $completion = $DB->get_record('course_completions', array(
            'userid' => $diploma_data['student_id'],
            'course' => $diploma_data['course_id']
        ));

        if (!$completion || !$completion->timecompleted) {
            return array(
                'valid' => false,
                'error' => 'Curso não foi concluído pelo estudante'
            );
        }

        // Obter dados do curso
        $course = $DB->get_record('course', array('id' => $diploma_data['course_id']));

        return array(
            'valid' => true,
            'student_name' => $user->firstname . ' ' . $user->lastname,
            'course_name' => $course ? $course->fullname : 'Curso não encontrado',
            'completion_date' => date('Y-m-d', $completion->timecompleted),
            'verification_date' => date('Y-m-d H:i:s')
        );

    } catch (Exception $e) {
        return array(
            'valid' => false,
            'error' => $e->getMessage()
        );
    }
}
