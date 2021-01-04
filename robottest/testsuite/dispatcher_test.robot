*** Settings ***
Library           String
Library           Collections
Library           RequestsLibrary
Library           OperatingSystem

*** Variables ***
# Credentials
${admin_user}=   Admin
${admin_pass}=   Admin
${test_user}=    %{TEST_USER}
${test_pass}=    %{TEST_PASS}
${test_email}=   %{TEST_EMAIL}
# Descriptors
${test_vnfd_pkg_bad}=   %{PACKAGES_DIR}/cirros_vnf.tar.gz
${test_vnfd_pkg_ok}=    %{PACKAGES_DIR}/hackfest_1_vnfd_fixed.tar.gz
${test_vnfd_pkg_image_dependency}=    %{PACKAGES_DIR}/monitored_vnf.tar.gz
${test_nsd_pkg_bad}=    %{PACKAGES_DIR}/cirros_2vnf_ns.tar.gz
${test_nsd_pkg_ok}=     %{PACKAGES_DIR}/hackfest_1_nsd_fixed.tar.gz
${test_nsd_pkg_vnf_dependency}=     %{PACKAGES_DIR}/fb_magma_ns.tar.gz


${test_nsd_id}=    hackfest1-ns

${test_experiment_bad}=   %{PACKAGES_DIR}/exp.json
${test_experiment_ok}=    %{PACKAGES_DIR}/exp_fixed.json

# VIM
${test_image_file}=   %{PACKAGES_DIR}/test_image2.qcow2
${vim_image_name}=    ubuntutest
${vim_name}=   %{VIM_NAME}


${dispatcher_URL}=   %{API_URL}

${true}=    Convert To Boolean    True
${false}=    Convert To Boolean    False


*** Keywords ***
Create Multi Part
    [Arguments]  ${addTo}  ${partName}  ${filePath}  ${contentType}=${None}  ${content}=${None}
    ${fileData}=  Run Keyword If  '''${content}''' != '''${None}'''  Set Variable  ${content}
    ...            ELSE  Get Binary File  ${filePath}
    ${fileDir}  ${fileName}=  Split Path  ${filePath}
    ${partData}=  Create List  ${fileName}  ${fileData}  ${contentType}
    Set To Dictionary  ${addTo}  ${partName}=${partData}

*** Test Cases ***

AUTH_REG_1 Register New User
    # Request preparation
    ${headers}=   create dictionary   Content-Type=application/x-www-form-urlencoded
    ${params}=   create dictionary   username=${test_user}    email=${test_email}   password=${test_pass}
    Create Session  alias=Dispatcher  url=${dispatcher_URL}   headers=${headers}   verify=${false}

    # Request
    ${resp}=   Post Request  Dispatcher   /auth/register   data=${params}

    # Output
    log   ${resp.json()}

    # VALIDATIONS
    #Should Be Equal As Strings  ${resp.json()['transaction']['status']}  success

    # If the user exists, it still should pass the test
    ${exists}=  Evaluate   "User already exists" in """${resp.text}"""
    Run Keyword If   '${exists}' == 'True'   Run Keyword   Should Be Equal As Strings    ${resp.status_code}   400
    ...               ELSE   Should Be Equal As Strings    ${resp.status_code}    200

AUTH_REG_2 Register failed due malformed email
    sleep  2s
# Request preparation
    ${headers}=   create dictionary   Content-Type=application/x-www-form-urlencoded
    ${params}=   create dictionary   username=${test_user}2    email=email_malformed  password=${test_pass}
    Create Session  alias=Dispatcher  url=${dispatcher_URL}   headers=${headers}   verify=${false}

    # Request
    ${resp}=   Post Request  Dispatcher   /auth/register   data=${params}

    # Output
    log   ${resp.json()}

    # VALIDATIONS
    #Should Be Equal As Strings  ${resp.json()['transaction']['status']}  success

    # If the user exists, it still should pass the test
    ${exists}=  Evaluate   "User already exists" in """${resp.text}"""
    Run Keyword If   '${exists}' == 'True'   Run Keyword   Should Be Equal As Strings    ${resp.status_code}   200
    ...               ELSE   Should Be Equal As Strings    ${resp.status_code}    400

AUTH_REG_3 Register failed due existing username
    sleep  2s
    # Request preparation
    ${headers}=   create dictionary   Content-Type=application/x-www-form-urlencoded
    ${params}=   create dictionary   username=${test_user}    email=2${test_email}   password=${test_pass}
    Create Session  alias=Dispatcher  url=${dispatcher_URL}   headers=${headers}   verify=${false}

    # Request
    ${resp}=   Post Request  Dispatcher   /auth/register   data=${params}

    # Output
    log   ${resp.json()}

    # VALIDATIONS
    #Should Be Equal As Strings  ${resp.json()['transaction']['status']}  success

    # If the user exists, it still should pass the test
    ${exists}=  Evaluate   "User already exists" in """${resp.text}"""
    Run Keyword If   '${exists}' == 'True'   Run Keyword   Should Be Equal As Strings    ${resp.status_code}   200
    ...               ELSE   Should Be Equal As Strings    ${resp.status_code}    400

AUTH_REG_4 Register failed due existing email
    sleep  2s
    # Request preparation
    ${headers}=   create dictionary   Content-Type=application/x-www-form-urlencoded
    ${params}=   create dictionary   username=${test_user}    email=2${test_email}   password=${test_pass}
    Create Session  alias=Dispatcher  url=${dispatcher_URL}   headers=${headers}   verify=${false}

    # Request
    ${resp}=   Post Request  Dispatcher   /auth/register   data=${params}

    # Output
    log   ${resp.json()}

    # VALIDATIONS
    #Should Be Equal As Strings  ${resp.json()['transaction']['status']}  success

    # If the user exists, it still should pass the test
    ${exists}=  Evaluate   "User already exists" in """${resp.text}"""
    Run Keyword If   '${exists}' == 'True'   Run Keyword   Should Be Equal As Strings    ${resp.status_code}   200
    ...               ELSE   Should Be Equal As Strings    ${resp.status_code}    400

AUTH_VAL_1 Validate User
    sleep  2s
    # Request preparation (Admin Basic Auth)
    ${headers}=   create dictionary   Content-Type=application/json  Authorization=Basic ABCDEF==
    ${auth}=  Create List  ${admin_user}  ${admin_pass}
    Create Session  alias=Dispatcher  url=${dispatcher_URL}  headers=${headers}  auth=${auth}   verify=${false}

    # Request
    ${resp}=   Put Request  Dispatcher   /auth/validate_user/${test_user}

    # VALIDATIONS
    Should Be Equal As Strings  ${resp.status_code}  200
    should contain   ${resp.text}    Changes applied

    # Output
    log   ${resp.json()}

AUTH_VAL_2 Validate no existing user
    sleep  2s
    # Request preparation (Admin Basic Auth)
    ${headers}=   create dictionary   Content-Type=application/json  Authorization=Basic ABCDEF==
    ${auth}=  Create List  ${admin_user}  ${admin_pass}
    Create Session  alias=Dispatcher  url=${dispatcher_URL}  headers=${headers}  auth=${auth}   verify=${false}

    # Request
    ${resp}=   Put Request  Dispatcher   /auth/validate_user/no${test_user}

    # VALIDATIONS
    Should Be Equal As Strings  ${resp.status_code}  400


    # Output
    log   ${resp.json()}

AUTH_VAL_3 Validate User already validated
    sleep  2s
    # Request preparation (Admin Basic Auth)
    ${headers}=   create dictionary   Content-Type=application/json  Authorization=Basic ABCDEF==
    ${auth}=  Create List  ${admin_user}  ${admin_pass}
    Create Session  alias=Dispatcher  url=${dispatcher_URL}  headers=${headers}  auth=${auth}   verify=${false}

    # Request
    ${resp}=   Put Request  Dispatcher   /auth/validate_user/${test_user}

    # VALIDATIONS
    Should Be Equal As Strings  ${resp.status_code}  200
    should contain   ${resp.text}    Changes applied

    # Output
    log   ${resp.json()}

AUTH_SHOW_1 Show Users (Admin Basic Auth)
    sleep  2s
    # Request preparation
    ${headers}=   create dictionary   Content-Type=application/json  Authorization=Basic ABCDEF==
    ${auth}=  Create List  ${admin_user}  ${admin_pass}
    Create Session  alias=Dispatcher  url=${dispatcher_URL}  headers=${headers}  auth=${auth}   verify=${false}

    # Request
    ${resp}=   Get Request  Dispatcher   /auth/show_users

    # VALIDATIONS
    Should Be Equal As Strings  ${resp.status_code}  200

    # Output
    log   ${resp.json()}


AUTH_TOK_1 Get User Token (User Basic Auth)
    sleep  5s
    # Request preparation
    ${headers}=   create dictionary   Content-Type=application/json  Authorization=Basic ABCDEF==
    ${auth}=  Create List  ${test_user}  ${test_pass}
    Create Session  alias=Dispatcher  url=${dispatcher_URL}  headers=${headers}  auth=${auth}   verify=${false}

    # Request
    ${resp}=   Get Request  Dispatcher   /auth/get_token

    # VALIDATIONS
    Should Be Equal As Strings  ${resp.status_code}  200

    # Output preparation
    ${token_aux}=   catenate   Bearer   ${resp.json()['result']}

    # Output
    Set Suite Variable   ${token}   ${token_aux}
    Log   ${token}

AUTH_TOK_2 Get User Token (no existing User Basic Auth)
    sleep  5s
    # Request preparation
    ${headers}=   create dictionary   Content-Type=application/json  Authorization=Basic ABCDEF==
    ${auth}=  Create List  a2${test_user}  ${test_pass}
    Create Session  alias=Dispatcher  url=${dispatcher_URL}  headers=${headers}  auth=${auth}   verify=${false}

    # Request
    ${resp}=   Get Request  Dispatcher   /auth/get_token

    # VALIDATIONS
    Should Be Equal As Strings  ${resp.status_code}  400

    # Output preparation
    ${token_aux}=   catenate   Bearer   ${resp.json()['result']}

    # Output
    Log   ${token}


WRAPPER_VIM_LIST_1 List VIMs (Token Auth)
    sleep  5s
    # Request preparation
    ${headers}=   create dictionary   Content-Type=application/json   Authorization=${token}
    Create Session  alias=Dispatcher  url=${dispatcher_URL}  headers=${headers}   verify=${false}

    # Request
    ${resp}=  Get Request  Dispatcher   /mano/vims

    # VALIDATIONS
    Log   ${resp.content}
    Should Contain  ${resp.text}   ${vim_name}
    Should Be Equal As Strings  ${resp.status_code}  200


WRAPPER_IMG_UPL_1 Upload Image VIM (Token Auth)
    sleep  5s
    # Request preparation
    ${headers}=   create dictionary   Authorization=${token}
    Create Session  alias=Dispatcher  url=${dispatcher_URL}   headers=${headers}   verify=${false}

    # Data
    &{data}=    Create Dictionary    vim_id=${vim_name}    container_format=bare
    ${file_data}=    Get Binary File    ${test_image_file}
    &{files}=    Create Dictionary    file=${file_data}

    ${resp}=    Post Request    Dispatcher   /mano/image   files=${files}    data=${data}

    # VALIDATIONS
    Log   ${resp.content}

    # If the image exists, it still should pass the test
    ${exists_in_openstack}=  Evaluate   "Image already exists" in """${resp.text}"""
    ${exists_in_opennebula}=  Evaluate   "NAME is already taken by IMAGE" in """${resp.text}"""
    Run Keyword If   '${exists_in_openstack}' == 'True' or '${exists_in_opennebula}' == 'True'   Run Keyword   Should Be Equal As Strings    ${resp.status_code}   400
    ...               ELSE   Should Be Equal As Strings    ${resp.status_code}    201

WRAPPER_IMG_UPL_2 Upload existing Image VIM (Token Auth)
    sleep  5s
    # Request preparation
    ${headers}=   create dictionary   Authorization=${token}
    Create Session  alias=Dispatcher  url=${dispatcher_URL}   headers=${headers}   verify=${false}

    # Data
    &{data}=    Create Dictionary    vim_id=${vim_name}    container_format=bare
    ${file_data}=    Get Binary File    ${test_image_file}
    &{files}=    Create Dictionary    file=${file_data}

    ${resp}=    Post Request    Dispatcher   /mano/image   files=${files}    data=${data}

    # VALIDATIONS
    Log   ${resp.content}

    # If the image exists, it still should pass the test
    ${exists_in_openstack}=  Evaluate   "Image already exists" in """${resp.text}"""
    ${exists_in_opennebula}=  Evaluate   "NAME is already taken by IMAGE" in """${resp.text}"""
    Run Keyword If   '${exists_in_openstack}' == 'True' or '${exists_in_opennebula}' == 'True'   Run Keyword   Should Be Equal As Strings    ${resp.status_code}   400
    ...               ELSE   Should Be Equal As Strings    ${resp.status_code}    201

WRAPPER_IMG_UPL_3 Upload wrong Image VIM (Token Auth)
    sleep  5s
    # Request preparation
    ${headers}=   create dictionary   Authorization=${token}
    Create Session  alias=Dispatcher  url=${dispatcher_URL}   headers=${headers}   verify=${false}

    # Data
    &{data}=    Create Dictionary    vim_id=${vim_name}    container_format=bare
    ${file_data}=    Get Binary File    ${test_image_file}
    &{files}=    Create Dictionary    file=incorrect_image.csv

    ${resp}=    Post Request    Dispatcher   /mano/image   files=${files}    data=${data}

    # VALIDATIONS
    Log   ${resp.content}

    # If the image exists, it still should pass the test
    Run Keyword Should Be Equal As Strings    ${resp.status_code}   400

WRAPPER_IMG_REG_1 Register VIM Image (Admin Basic Auth)
    sleep  5s
    # Request preparation
    ${headers}=   create dictionary   Authorization=Basic ABCDEF==
    ${auth}=  Create List   ${admin_user}   ${admin_pass}
    Create Session  alias=Dispatcher  url=${dispatcher_URL}  headers=${headers}  auth=${auth}   verify=${false}

    # Data
    ${data}=   Evaluate   [('vim_id', '${vim_name}'), ('image_name', '${vim_image_name}')]

    ${resp}=    Post Request    Dispatcher   /mano/image   data=${data}

    # VALIDATIONS
    Log   ${resp.content}
    Should Be Equal As Strings    ${resp.status_code}    201

WRAPPER_IMG_REG_2 Register VIM Image (User without permisions Basic Auth)
    sleep  5s
    # Request preparation
    ${headers}=   create dictionary   Authorization=Basic ABCDEF==
    ${auth}=  Create List   ${test_user}   ${test_pass}
    Create Session  alias=Dispatcher  url=${dispatcher_URL}  headers=${headers}  auth=${auth}   verify=${false}

    # Data
    ${data}=   Evaluate   [('vim_id', '${vim_name}'), ('image_name', '${vim_image_name}')]

    ${resp}=    Post Request    Dispatcher   /mano/image   data=${data}

    # VALIDATIONS
    Log   ${resp.content}
    Should Be Equal As Strings    ${resp.status_code}    201

WRAPPER_IMG_LIST_1 Get Image List (Token Auth)
    sleep  5s
    # Request preparation
    ${headers}=   create dictionary   Authorization=${token}
    ${false}=    Convert To Boolean    False
    Create Session  alias=Dispatcher  url=${dispatcher_URL}   headers=${headers}   verify=${false}

    ${resp}=    Get Request    Dispatcher   /mano/image

    # VALIDATIONS
    log    ${resp.content}
    Should Be Equal As Strings    ${resp.status_code}    200

WRAPPER_VNF_INDEX_1 Index VNFD (Token Auth)
    sleep  5s
    # Request preparation
    ${headers}=   create dictionary   Authorization=${token}
    Create Session  alias=Dispatcher  url=${dispatcher_URL}   headers=${headers}   verify=${false}

    # Data
    &{data}=    Create Dictionary    visibility=True
    ${file_data}=    Get Binary File    ${test_vnfd_pkg_ok}
    &{files}=    Create Dictionary    file=${file_data}

    ${resp}=    Post Request    Dispatcher   /mano/vnfd    files=${files}    data=${data}

    # VALIDATIONS
    Log    ${resp.content}
    Should Be Equal As Strings    ${resp.status_code}    200

WRAPPER_VNF_INDEX_2 Index existing VNFD (Token Auth)
    sleep  5s
    # Request preparation
    ${headers}=   create dictionary   Authorization=${token}
    Create Session  alias=Dispatcher  url=${dispatcher_URL}   headers=${headers}   verify=${false}

    # Data
    &{data}=    Create Dictionary    visibility=True
    ${file_data}=    Get Binary File    ${test_vnfd_pkg_ok}
    &{files}=    Create Dictionary    file=${file_data}

    ${resp}=    Post Request    Dispatcher   /mano/vnfd    files=${files}    data=${data}

    # VALIDATIONS
    Log    ${resp.content}
    Should Be Equal As Strings    ${resp.status_code}    200

WRAPPER_VNF_INDEX_3 Index Faulty VNFD (Token Auth)
    sleep  5s
    # Request preparation
    ${headers}=   create dictionary   Authorization=${token}
    Create Session  alias=Dispatcher  url=${dispatcher_URL}   headers=${headers}   verify=${false}

    # Data
    &{data}=    Create Dictionary    visibility=True
    ${file_data}=    Get Binary File    ${test_vnfd_pkg_bad}
    &{files}=    Create Dictionary    file=${file_data}

    ${resp}=    Post Request    Dispatcher   /mano/vnfd    files=${files}    data=${data}

    # VALIDATIONS
    Log    ${resp.content}
    ${error} =  Get From Dictionary  ${resp.json()}   error
    Should Be Equal  ${error}   Some VNFs have invalid descriptors
    #Should Be Equal As Strings  ${resp.json()['error']}   Some VNFs have invalid descriptors
    Should Be Equal As Strings    ${resp.status_code}    400

WRAPPER_VNF_INDEX_4 Index VNFD (Token Auth)
    sleep  5s
    # Request preparation
    ${headers}=   create dictionary   Authorization=${token}
    Create Session  alias=Dispatcher  url=${dispatcher_URL}   headers=${headers}   verify=${false}

    # Data
    &{data}=    Create Dictionary    visibility=True
    ${file_data}=    Get Binary File    ${test_vnfd_pkg_image_dependency}
    &{files}=    Create Dictionary    file=${file_data}

    ${resp}=    Post Request    Dispatcher   /mano/vnfd    files=${files}    data=${data}

    # VALIDATIONS
    Log    ${resp.content}
    Should Be Equal As Strings    ${resp.status_code}    200


WRAPPER_VNF_LIST_1 Get VNFD list (Token Auth)
    sleep  5s
    # Request preparation
    ${headers}=   create dictionary   Content-Type=application/json  Authorization=${token}
    Create Session  alias=Dispatcher  url=${dispatcher_URL}  headers=${headers}   verify=${false}

    # Request
    ${resp}=  Get Request  Dispatcher   /mano/vnfd

    # VALIDATIONS
    Log    ${resp.content}
    Should Be Equal As Strings  ${resp.status_code}  200

WRAPPER_NS_INDEX_1 Index NSD (Token Auth)
    sleep  5s
    # Request preparation
    ${headers}=   create dictionary   Authorization=${token}
   Create Session  alias=Dispatcher  url=${dispatcher_URL}   headers=${headers}   verify=${false}

    # Data
    &{data}=    Create Dictionary    visibility=True
    ${file_data}=    Get Binary File    ${test_nsd_pkg_ok}
    &{files}=    Create Dictionary    file=${file_data}

    ${resp}=    Post Request    Dispatcher   /mano/nsd    files=${files}    data=${data}

    # VALIDATIONS
    Log    ${resp.content}
    Should Be Equal As Strings    ${resp.status_code}    200

WRAPPER_NS_INDEX_2 Index existing NSD (Token Auth)
    sleep  5s
    # Request preparation
    ${headers}=   create dictionary   Authorization=${token}
   Create Session  alias=Dispatcher  url=${dispatcher_URL}   headers=${headers}   verify=${false}

    # Data
    &{data}=    Create Dictionary    visibility=True
    ${file_data}=    Get Binary File    ${test_nsd_pkg_ok}
    &{files}=    Create Dictionary    file=${file_data}

    ${resp}=    Post Request    Dispatcher   /mano/nsd    files=${files}    data=${data}

    # VALIDATIONS
    Log    ${resp.content}
    Should Be Equal As Strings    ${resp.status_code}    200

WRAPPER_NS_INDEX_3 Index Faulty NSD (Token Auth)
    sleep  5s
    # Request preparation
    ${headers}=   create dictionary   Authorization=${token}
    Create Session  alias=Dispatcher  url=${dispatcher_URL}   headers=${headers}   verify=${false}

    # Data
    &{data}=    Create Dictionary    visibility=True
    ${file_data}=    Get Binary File    ${test_nsd_pkg_bad}
    &{files}=    Create Dictionary    file=${file_data}

    ${resp}=    Post Request    Dispatcher   /mano/nsd    files=${files}    data=${data}

    # VALIDATIONS
    Log    ${resp.content}
    ${error} =  Get From Dictionary  ${resp.json()}   error
    Should Be Equal  ${error}   Some NSD have invalid descriptors
    #Should Be Equal As Strings  ${resp.json()['error']}   Some NSD have invalid descriptors
    Should Be Equal As Strings    ${resp.status_code}    400

WRAPPER_NS_INDEX_4 Index Faulty NSD (Token Auth)
    sleep  5s
    # Request preparation
    ${headers}=   create dictionary   Authorization=${token}
    Create Session  alias=Dispatcher  url=${dispatcher_URL}   headers=${headers}   verify=${false}

    # Data
    &{data}=    Create Dictionary    visibility=True
    ${file_data}=    Get Binary File    ${test_nsd_pkg_vnf_dependency}
    &{files}=    Create Dictionary    file=${file_data}

    ${resp}=    Post Request    Dispatcher   /mano/nsd    files=${files}    data=${data}

    # VALIDATIONS
    Log    ${resp.content}
    ${error} =  Get From Dictionary  ${resp.json()}   error
    Should Be Equal  ${error}   Some NSD have invalid descriptors
    #Should Be Equal As Strings  ${resp.json()['error']}   Some NSD have invalid descriptors
    Should Be Equal As Strings    ${resp.status_code}    400

WRAPPER_NS_LIST_1 Get NSD list (Token Auth)
    sleep  5s
    # Request preparation
    ${headers}=   create dictionary   Content-Type=application/json  Authorization=${token}
    Create Session  alias=Dispatcher  url=${dispatcher_URL}  headers=${headers}   verify=${false}

    # Request
    ${resp}=  Get Request  Dispatcher   /mano/nsd

    # VALIDATIONS
    Log    ${resp.content}
    Should Be Equal As Strings  ${resp.status_code}  200


Validate Bad Experiment Descriptor
    sleep  5s
    # Request preparation
    ${headers}=   create dictionary   Authorization=${token}
    Create Session  alias=Dispatcher  url=${dispatcher_URL}   headers=${headers}   verify=${false}

    # Data
    ${file_data}=    Get File    ${test_experiment_bad}

    ${resp}=    Post Request    Dispatcher   /elcm/validate/ed    data=${file_data}

    # VALIDATIONS
   Log   ${resp.json()}
    Should Be Equal As Strings    ${resp.status_code}    400


Validate Experiment Descriptor
    sleep  5s
    # Request preparation
    ${headers}=   create dictionary   Authorization=${token}
    Create Session  alias=Dispatcher  url=${dispatcher_URL}   headers=${headers}   verify=${false}

    # Data
    ${file_data}=    Get File    ${test_experiment_ok}

    ${resp}=    Post Request    Dispatcher   /elcm/validate/ed    data=${file_data}

    # VALIDATIONS
    Log   ${resp.json()}
    Should Be Equal As Strings    ${resp.status_code}    200


Onboard NSD (Token Auth)
    sleep  5s
    # Request preparation
    ${headers}=   create dictionary   Authorization=${token}
    #${headers}=   create dictionary   Content-Type=multipart/form-data   Authorization=${token}
    Create Session  alias=Dispatcher  url=${dispatcher_URL}   headers=${headers}   verify=${false}

    # Data
    ${data}=   Evaluate   [('ns', '${test_nsd_id}')]

    ${resp}=    Post Request    Dispatcher   /mano/onboard   data=${data}

    # VALIDATIONS
    log   ${resp.json()}
    Should Be Equal As Strings    ${resp.status_code}    201


Delete NSD
    sleep  5s
    # Request preparation
    ${headers}=   create dictionary   Content-Type=multipart/form-data   Authorization=${token}
    Create Session  alias=Dispatcher  url=${dispatcher_URL}   headers=${headers}   verify=${false}

    # Data
    &{data}=    Create Dictionary    all=True

    ${resp}=    Delete Request    Dispatcher   /mano/nsd/${test_nsd_id}    data=${data}

    # VALIDATIONS
    Should Be Equal As Strings    ${resp.status_code}    204


Delete User (Admin Basic Auth)
    # Request preparation
    ${headers}=   create dictionary   Content-Type=application/json  Authorization=Basic ABCDEF==
    ${auth}=  Create List  ${admin_user}  ${admin_pass}
    Create Session  alias=Dispatcher  url=${dispatcher_URL}  headers=${headers}  auth=${auth}   verify=${false}

    # Request
    ${resp}=   Delete Request  Dispatcher   /auth/delete_user/${test_user}

    # VALIDATIONS
    ${result} =  Get From Dictionary  ${resp.json()}   result
    Should Contain  ${result}   user is removed
    Should Be Equal As Strings  ${resp.status_code}  200


Drop Database (Admin Basic Auth)
    # Request preparation
    ${headers}=   create dictionary   Content-Type=application/json  Authorization=Basic ABCDEF==
    ${auth}=  Create List  ${admin_user}  ${admin_pass}
    Create Session  alias=Dispatcher  url=${dispatcher_URL}  headers=${headers}  auth=${auth}   verify=${false}

    # Request
    ${resp}=   Delete Request  Dispatcher   /auth/drop_db

    # VALIDATIONS
    Should Be Equal As Strings  ${resp.status_code}  200

