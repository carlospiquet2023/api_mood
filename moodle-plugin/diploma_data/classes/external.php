<?php
/**
 * Classe externa para API do plugin diploma_data
 * 
 * Esta classe implementa as funções que serão expostas via webservice
 * para o sistema de automatização de diplomas.
 * 
 * @package    local_diploma_data
 * @copyright  2025 Carlos Antonio de Oliveira Piquet
 * @author     Carlos Antonio de Oliveira Piquet <carlospiquet.projetos@gmail.com>
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

defined('MOODLE_INTERNAL') || die();

require_once($CFG->libdir . "/externallib.php");
require_once($CFG->dirroot . '/course/lib.php');
require_once($CFG->dirroot . '/user/profile/lib.php');
require_once($CFG->dirroot . '/user/lib.php');
require_once($CFG->dirroot . '/lib/completionlib.php');
require_once($CFG->dirroot . '/lib/enrollib.php');

/**
 * Classe principal para funções externas do diploma_data
 */
class local_diploma_data_external extends external_api {

    /**
     * Parâmetros para get_user_diploma_details
     */
    public static function get_user_diploma_details_parameters() {
        return new external_function_parameters(
            array(
                'userid' => new external_value(PARAM_INT, 'ID do utilizador'),
                'courseid' => new external_value(PARAM_INT, 'ID do curso', VALUE_OPTIONAL, 0)
            )
        );
    }

    /**
     * Obtém dados completos do utilizador para diploma
     */
    public static function get_user_diploma_details($userid, $courseid = 0) {
        global $DB, $CFG;

        // Validar parâmetros
        $params = self::validate_parameters(
            self::get_user_diploma_details_parameters(),
            array('userid' => $userid, 'courseid' => $courseid)
        );
        
        // Verificar contexto e permissões
        $context = context_system::instance();
        self::validate_context($context);
        require_capability('moodle/user:viewdetails', $context);

        try {
            $user = $DB->get_record('user', array('id' => $params['userid']), '*', MUST_EXIST);
            
            if ($user->deleted) {
                throw new moodle_exception('userdeleted', 'error');
            }

            profile_load_custom_fields($user);
            
            $customfields = array();
            if (!empty($user->profile)) {
                foreach ($user->profile as $fieldname => $fieldvalue) {
                    $customfields[] = array('name' => $fieldname, 'value' => $fieldvalue);
                }
            }

            $user_courses = array();
            if ($params['courseid'] > 0) {
                $course = $DB->get_record('course', array('id' => $params['courseid']), '*', MUST_EXIST);
                $completion = self::get_course_completion_data($user->id, $course->id);
                
                $user_courses[] = array(
                    'id' => $course->id,
                    'fullname' => $course->fullname,
                    'shortname' => $course->shortname,
                    'completion' => $completion
                );
            } else {
                $enrolled_courses = enrol_get_users_courses($user->id, true);
                foreach ($enrolled_courses as $course) {
                    $completion = self::get_course_completion_data($user->id, $course->id);
                    $user_courses[] = array(
                        'id' => $course->id,
                        'fullname' => $course->fullname,
                        'shortname' => $course->shortname,
                        'completion' => $completion
                    );
                }
            }

            return array(
                'status' => 'success',
                'user' => array(
                    'id' => $user->id,
                    'username' => $user->username,
                    'firstname' => $user->firstname,
                    'lastname' => $user->lastname,
                    'fullname' => fullname($user),
                    'email' => $user->email,
                    'customfields' => $customfields
                ),
                'courses' => $user_courses,
                'timestamp' => time()
            );

        } catch (Exception $e) {
            return array('status' => 'error', 'message' => $e->getMessage(), 'timestamp' => time());
        }
    }

    /**
     * Estrutura de retorno para get_user_diploma_details
     */
    public static function get_user_diploma_details_returns() {
        return new external_single_structure(
            array(
                'status' => new external_value(PARAM_TEXT, 'Status da operação'),
                'user' => new external_single_structure(
                    array(
                        'id' => new external_value(PARAM_INT, 'ID do utilizador'),
                        'username' => new external_value(PARAM_TEXT, 'Username'),
                        'firstname' => new external_value(PARAM_TEXT, 'Primeiro nome'),
                        'lastname' => new external_value(PARAM_TEXT, 'Último nome'),
                        'fullname' => new external_value(PARAM_TEXT, 'Nome completo'),
                        'email' => new external_value(PARAM_EMAIL, 'Email'),
                        'customfields' => new external_multiple_structure(
                            new external_single_structure(
                                array(
                                    'name' => new external_value(PARAM_TEXT, 'Nome do campo'),
                                    'value' => new external_value(PARAM_RAW, 'Valor do campo')
                                )
                            ), 'Campos personalizados', VALUE_OPTIONAL
                        )
                    ), 'Dados do utilizador', VALUE_OPTIONAL
                ),
                'courses' => new external_multiple_structure(
                    new external_single_structure(
                        array(
                            'id' => new external_value(PARAM_INT, 'ID do curso'),
                            'fullname' => new external_value(PARAM_TEXT, 'Nome completo do curso'),
                            'shortname' => new external_value(PARAM_TEXT, 'Nome curto do curso'),
                            'completion' => new external_single_structure(
                                array(
                                    'completed' => new external_value(PARAM_BOOL, 'Curso completado'),
                                    'timecompleted' => new external_value(PARAM_INT, 'Timestamp de conclusão', VALUE_OPTIONAL),
                                    'grade' => new external_value(PARAM_FLOAT, 'Nota final', VALUE_OPTIONAL)
                                ), 'Dados de conclusão', VALUE_OPTIONAL
                            )
                        )
                    ), 'Cursos do utilizador', VALUE_OPTIONAL
                ),
                'message' => new external_value(PARAM_TEXT, 'Mensagem de erro', VALUE_OPTIONAL),
                'timestamp' => new external_value(PARAM_INT, 'Timestamp da resposta')
            )
        );
    }

    /**
     * Parâmetros para search_users
     */
    public static function search_users_parameters() {
        return new external_function_parameters(
            array(
                'search_term' => new external_value(PARAM_TEXT, 'Termo de busca para nome ou email')
            )
        );
    }

    /**
     * Busca utilizadores por nome ou email
     */
    public static function search_users($search_term) {
        global $DB;

        $params = self::validate_parameters(
            self::search_users_parameters(),
            array('search_term' => $search_term)
        );

        $context = context_system::instance();
        self::validate_context($context);
        require_capability('moodle/user:viewdetails', $context);

        try {
            $search_term = trim($params['search_term']);
            $sql_search = '%' . $DB->sql_like_escape($search_term) . '%';

            $sql = "SELECT id, firstname, lastname, email, username 
                    FROM {user} 
                    WHERE deleted = 0 
                    AND (CONCAT(firstname, ' ', lastname) LIKE ? OR email LIKE ?)
                    ORDER BY firstname, lastname 
                    LIMIT 20";

            $users_found = $DB->get_records_sql($sql, array($sql_search, $sql_search));

            $results = array();
            foreach ($users_found as $user) {
                $results[] = array(
                    'id' => $user->id,
                    'firstname' => $user->firstname,
                    'lastname' => $user->lastname,
                    'fullname' => fullname($user),
                    'email' => $user->email,
                    'username' => $user->username
                );
            }

            return array('status' => 'success', 'users' => $results);

        } catch (Exception $e) {
            return array('status' => 'error', 'message' => $e->getMessage());
        }
    }

    /**
     * Estrutura de retorno para search_users
     */
    public static function search_users_returns() {
        return new external_single_structure(
            array(
                'status' => new external_value(PARAM_TEXT, 'Status da operação'),
                'users' => new external_multiple_structure(
                    new external_single_structure(
                        array(
                            'id' => new external_value(PARAM_INT, 'ID do utilizador'),
                            'firstname' => new external_value(PARAM_TEXT, 'Primeiro nome'),
                            'lastname' => new external_value(PARAM_TEXT, 'Último nome'),
                            'fullname' => new external_value(PARAM_TEXT, 'Nome completo'),
                            'email' => new external_value(PARAM_EMAIL, 'Email'),
                            'username' => new external_value(PARAM_TEXT, 'Username')
                        )
                    ), 'Lista de utilizadores encontrados', VALUE_OPTIONAL
                ),
                'message' => new external_value(PARAM_TEXT, 'Mensagem de erro', VALUE_OPTIONAL)
            )
        );
    }

    /**
     * Função auxiliar para obter dados de conclusão do curso
     */
    private static function get_course_completion_data($userid, $courseid) {
        global $DB, $CFG;

        $completion_data = array(
            'completed' => false,
            'timecompleted' => null,
            'grade' => null
        );

        if (empty($CFG->enablecompletion)) {
            return $completion_data;
        }

        $completion_record = $DB->get_record('course_completions', 
            array('userid' => $userid, 'course' => $courseid));
        
        if ($completion_record && $completion_record->timecompleted) {
            $completion_data['completed'] = true;
            $completion_data['timecompleted'] = $completion_record->timecompleted;
        }

        $grade_item = $DB->get_record('grade_items', 
            array('courseid' => $courseid, 'itemtype' => 'course'));
        
        if ($grade_item) {
            $grade_grade = $DB->get_record('grade_grades', 
                array('itemid' => $grade_item->id, 'userid' => $userid));
            
            if ($grade_grade && !is_null($grade_grade->finalgrade)) {
                $completion_data['grade'] = round($grade_grade->finalgrade, 2);
            }
        }

        return $completion_data;
    }
}
