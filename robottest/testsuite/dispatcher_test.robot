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
${test_nsd_pkg_bad}=    %{PACKAGES_DIR}/cirros_2vnf_ns.tar.gz
${test_nsd_pkg_ok}=     %{PACKAGES_DIR}/hackfest_1_nsd_fixed.tar.gz
${test_nsd_id}=    hackfest1-ns

${test_experiment_bad}=   %{PACKAGES_DIR}/exp.json
${test_experiment_ok}=    %{PACKAGES_DIR}/exp_fixed.json

# VIM
${test_image_file}=   %{PACKAGES_DIR}/%{TEST_IMAGE}
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

Register New User
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


Validate User
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


Show Users (Admin Basic Auth)
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


Get User Token (User Basic Auth)
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


List VIMs (Token Auth)
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


Upload Image VIM (Token Auth)
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


Register VIM Image (Admin Basic Auth)
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


Get Image List (Token Auth)
    sleep  5s
    # Request preparation
    ${headers}=   create dictionary   Authorization=${token}
    ${false}=    Convert To Boolean    False
    Create Session  alias=Dispatcher  url=${dispatcher_URL}   headers=${headers}   verify=${false}

    ${resp}=    Get Request    Dispatcher   /mano/image

    # VALIDATIONS
    log    ${resp.content}
    Should Be Equal As Strings    ${resp.status_code}    200


Index Faulty VNFD (Token Auth)
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


Index VNFD (Token Auth)
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


Get VNFD list (Token Auth)
    sleep  5s
    # Request preparation
    ${headers}=   create dictionary   Content-Type=application/json  Authorization=${token}
    Create Session  alias=Dispatcher  url=${dispatcher_URL}  headers=${headers}   verify=${false}

    # Request
    ${resp}=  Get Request  Dispatcher   /mano/vnfd

    # VALIDATIONS
    Log    ${resp.content}
    Should Be Equal As Strings  ${resp.status_code}  200


Get VNFD list (Basic Auth)
    sleep  5s
    # Request preparation
    ${headers}=   create dictionary   Content-Type=application/json   Authorization=Basic ABCDEF==
    ${auth}=  Create List   ${test_user}   ${test_pass}
    Create Session  alias=Dispatcher  url=${dispatcher_URL}  headers=${headers}  auth=${auth}   verify=${false}

    # Request
    ${resp}=  Get Request  Dispatcher   /mano/vnfd

    # VALIDATIONS
    Log    ${resp.content}
    Should Be Equal As Strings  ${resp.status_code}  200


Index Faulty NSD (Token Auth)
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


Index NSD (Token Auth)
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


Get NSD list (Token Auth)
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


