##########################################################################################################
# Instructions                                                                                           #
# 1. create a main folder e.g pmd1                                                                       #
# 2. create a subfolder where all the library files will be kept e.g. checks_lib                         #
#   2a. past your customised rules set file into the checks_libs subfolder e.g. pmdrules.xml             #
# 3. create a subfolders where all the mvn apps will be saved e.g. mvn_apps                              #
# 4. update all the directories in the sbatch script to reflect your current directory                   #
# 5. run the sbatch script e.g. sbatch s1_mk_multiple_maven_apps_n_move_files_ARR.sl                     #
# 6. run the sbatch script e.g. sbatch pmdrules.xml                                                      #
##########################################################################################################

# Read this Post for runing processis in parallel
# https://stackoverflow.com/questions/42979271/how-to-run-multiple-instances-of-the-same-python-script-which-uses-subprocess-ca
# 
# How to use this program
# srun python s1_mk_multiple_maven_apps_n_move_files_ARR.py -idx "${SLURM_ARRAY_TASK_ID}" -n 577 -s ../my_codesnippet_analysis/pmdpasscodesnippets_java -pd ../my_codesnippet_analysis/pmd1/mvn_apps -upd -libs ../my_codesnippet_analysis/pmd1/checks_lib -rvaf

# srun python s1_mk_multiple_maven_apps_n_move_files_ARR.py -idx "${SLURM_ARRAY_TASK_ID}" -n 577 -s ../my_codesnippet_analysis/codesnippets_java -crd ../my_codesnippet_analysis/pmd1 -ucrd -pd mvn_apps -upd -libs checks_lib -rvaf

# Change the data source -s
# ../../../../stackexchange_v2/workspace/input/codesnippets_csv

# To run it on slum:
# $    sbatch s1_mk_multiple_maven_apps_n_move_files_ARR.sl 


# Fetch the Files 
# Divide the Files equaliy according to the number
# Generate the Maven Applications based on the number of files
# delete the initial App.java file created by default
# Update the Pom.xml File to suite
# add google check.xml


import subprocess as sp
# what will be used to read files
import glob
import shutil
import os
import numpy as np
import re

import xml.etree.ElementTree as ET
#from xml.dom import minidom

import argparse

parser = argparse.ArgumentParser(
    description='Run CheckStyle on Java Apps.'
)

parser.add_argument(
    "-idx",
    "--arrayid",
    default="java",
    type=str,
    help="Enter SLURM ARRAY TASK ID"
)

parser.add_argument(
    "-n",
    "--size",
    default=577,
    type=int,
    help="Enter number of jobs to execute"
)

#e.g. ../my_codesnippet_analysis/pmdpasscodesnippets_java
parser.add_argument(
    "-s",
    "--source",
    help="Enter the location of the source folder to fetch (copy or move) the source code files from e.g java, py, cpp"
)

# command -mv ---> sets mv to True
# command --->sets mv to False
#https://stackoverflow.com/questions/60999816/argparse-not-parsing-boolean-arguments
parser.add_argument(
    "-mv",
    "--movesource", 
    action="store_true",
    help="Move rather than copy the source codes files"
)

parser.add_argument(
    "-t",
    "--sourcetype",
    default="java",
    type=str,
    help="Enter source type java, py, cpp"
)

parser.add_argument(
    "-ucrd",
    "--usecommonrootdir",
    action="store_true",
    help="Use common root directory"
)
#e.g. ../my_codesnippet_analysis/pmd1
parser.add_argument(
    "-crd",
    "--commonrootdir",
    help="Use common root directory"
)

parser.add_argument(
    "-upd",
    "--useparentdest",
    action="store_true",
     help="Agree to use parent destination"   
)

#e.g. ../my_codesnippet_analysis/pmd1/mvn_apps
parser.add_argument(
    "-pd",
    "--parentdest",
    default=".",
    type=str, 
     help="Parent path where multiple folders will be generated (before the autogenerated folders)"   
)

parser.add_argument(
    "-a",
    "--app",
    default='my-javacodeanalysis-app',
    help="Enter general application name that will be auto generated e.g my-javacodeanalysis-app with will be appended with numbers 0, 1, ..., n"
)

parser.add_argument(
    "-cd",
    "--childdest",
    default="src/main/java",
    type=str, 
     help="The child destination path(s) where the multiple subfolders you want to copy files to (after the autogenerated folders)"
)


# command -rvaf ---> sets rva to True
# command --->sets rv to False
#https://stackoverflow.com/questions/60999816/argparse-not-parsing-boolean-arguments
parser.add_argument(
    "-rvaf",
    "--removeautogenfile", 
    action="store_true",
    help="removes the previous apps if they exist before creating a new one"
)
parser.add_argument(
    "-raf",
    "--autogenfileremove",
    default="App.java",
    type=str,
    help="Enter the name of an auto generated class that is created along with the maven app that you want removed. e.g App.java"
)

parser.add_argument(
    "-p",
    "--pkg",
    default='myjavacodeanalysis',
    help="Enter the package name you want each class to have or the java files to be moved to"
)

parser.add_argument(
    "-cst",
    "--compilersourcetarget", 
    default="17",
    type=str,
    help="Enter the check style version"
)


#parser.add_argument(
#    "-ppyv",
#    "--puppyversion", 
#    default="9.1",
#    type=str,
#    help="Enter the check style version"
#)

parser.add_argument(
    "-mpv",
    "--mavenpmdpluginversion", 
    default="3.15.0",
    type=str,
    help="Enter the maven checkstyle plugin version"
)

parser.add_argument(
    "-mpp",
    "--mavenpmdplugin", 
    default="maven-pmd-plugin",
    type=str,
    help="Enter the maven checkstyle plugin"
)

parser.add_argument(
    "-pru",
    "--pmdxmlrules", 
    default="pmdrules.xml",
    type=str,
    help="Enter the full name of the checks file plus extension (default is the pmdrules.xml which will be auto included in the root directory where the pom.xml is located)."
)

# e.g. checks_lib
parser.add_argument(
    "-libs",
    "--libdir", 
    default="",
    type=str,
    help="Enter the path to copy the checks file from."
)


parser.add_argument(
     "-pt",
    "--pattern",
    default="",
    type=str,
    help="Are there particular pattern of files you want to select."
)
 

args = parser.parse_args()

array_id = args.arrayid
size = args.size
java_app = args.app
java_pkg = args.pkg
src_fdr = args.source
src_type = args.sourcetype
mv_src = args.movesource
rm_auto_gen_file = args.removeautogenfile
auto_gen_file_rm = args.autogenfileremove
use_comm_root_dir = args.usecommonrootdir
comm_root_dir = args.commonrootdir
pattern = args.pattern
use_parent_dest_path = args.useparentdest
parent_dest_path = args.parentdest
child_dest_path = args.childdest
compiler_source_tagret = args.compilersourcetarget
#puppy_version = args.puppyversion
maven_pmd_plugin_version = args.mavenpmdpluginversion
maven_pmd_plugin = args.mavenpmdplugin
pmd_xml_rules = args.pmdxmlrules
lib_path = args.libdir

pkg_name_full=java_pkg
app_name_partial=java_app


# Get the directory of all the files to be read from
# get the directory to where the *.java files in the pmdpasscodesnippets_java path or folder
#file_location = os.path.join('../my_codesnippet_analysis/codesnippets_java', '*.java')
file_location = os.path.join(src_fdr, '{}*.{}'.format(pattern, src_type))

# get all the file names and their paths
filenames = glob.glob(file_location)

# number of files
print('Total number of Java Files {}'.format(len(filenames)))

# splits N files into n equal parts
split_filenames = np.array_split(filenames, size)

########################################################
# Updates the pom.xml file with pmd requirements #
########################################################
def update_pom_xml(
    app_name
):
    
    ####### Retrieve the pom.xml file from the java app #######
    pom_xml = '{}/pom.xml'.format(app_name)
    #tree = ET.parse('pom.xml')
    tree = ET.parse(pom_xml)
    
    root = tree.getroot()

    ###### Register namespace ######
    # retrieve 'http://maven.apache.org/POM/4.0.0' from root tag '{http://maven.apache.org/POM/4.0.0}project'
    pattern = re.compile(r'(https?:\/\/(www\.)?\w+\.\w+.\w+\/\w+\/\d+\.\d+\.\d)')
    root_namespace = pattern.findall(root.tag)[0][0]
   
    #ET.register_namespace('', "http://maven.apache.org/POM/4.0.0")
    ET.register_namespace('', root_namespace)

    # instantiate empty attributes
    attrib = {}

    ######### update the 'properties' source and target text tag with the pmd requirements ##########
    # <properties>
    properties = root[6]
    # <properties><maven.compiler.source>
    source = properties[1]
    # <properties><maven.compiler.target>
    target = properties[2]
    
    # update the text
    source.text = compiler_source_tagret #17
    target.text = compiler_source_tagret #17
    
    ######### update the 'build' tag with the pmd requirements ##########
    # get the build
    # <build>
    build = root[8]
    # <build><pluginManagement>
    pluginManagement = build[0]
    # <build><pluginManagement><plugins>
    plugins = pluginManagement[0]

    # <build><pluginManagement><plugins><plugin>
    plugin = plugins.makeelement('plugin', attrib)
    plugins.append(plugin)

    # <build><pluginManagement><plugins><plugin><groupId>
    groupId = plugin.makeelement('groupId', attrib)
    groupId.text = 'org.apache.maven.plugins'
    plugin.append(groupId)

    # <build><pluginManagement><plugins><plugin><artifactId>
    artifactId = plugin.makeelement('artifactId', attrib)
    artifactId.text = maven_pmd_plugin
    plugin.append(artifactId)

    # <build><pluginManagement><plugins><plugin><version>
    version = plugin.makeelement('version', attrib)
    version.text = maven_pmd_plugin_version
    plugin.append(version)


    # <build><pluginManagement><plugins><plugin><dependencies>
    #dependencies = plugin.makeelement('dependencies', attrib)
    #plugin.append(dependencies)

    # <build><pluginManagement><plugins><plugin><dependencies><dependency>
    #dependency = dependencies.makeelement('dependency', attrib)
    #dependencies.append(dependency)

    # <build><pluginManagement><plugins><plugin><dependencies><dependency><groupId>
    #groupId = dependency.makeelement('groupId', attrib)
    #groupId.text = 'com.puppycrawl.tools'
    #dependency.append(groupId)

    # <build><pluginManagement><plugins><plugin><dependencies><dependency><artifactId>
    #artifactId = dependency.makeelement('artifactId', attrib)
    #artifactId.text = 'pmd'
    #dependency.append(artifactId)

    # <build><pluginManagement><plugins><plugin><dependencies><dependency><version>
    #version = dependency.makeelement('version', attrib)
    #version.text = puppy_version
    #dependency.append(version)

    # <build><pluginManagement><plugins><plugin><executions>
    executions = plugin.makeelement('executions', attrib)
    plugin.append(executions)

    # <build><pluginManagement><plugins><plugin><executions><execution>
    execution = executions.makeelement('execution', attrib)
    executions.append(execution)

    # <build><pluginManagement><plugins><plugin><executions><execution><id>
    ids = execution.makeelement('id', attrib)
    ids.text = 'pmd'
    execution.append(ids)

    # <build><pluginManagement><plugins><plugin><executions><execution><phase>
    phase = execution.makeelement('phase', attrib)
    phase.text = 'validate'
    execution.append(phase)

    # <build><pluginManagement><plugins><plugin><executions><execution><goals>
    goals = execution.makeelement('goals', attrib)
    execution.append(goals)

    # <build><pluginManagement><plugins><plugin><executions><execution><goals><goal>
    goal = goals.makeelement('goal', attrib)
    goal.text = 'check'
    goals.append(goal)

    # <build><pluginManagement><plugins><plugin><executions><execution><configuration>
    configuration = execution.makeelement('configuration', attrib)
    execution.append(configuration)

    # <build><pluginManagement><plugins><plugin><executions><execution><configuration><rulesets>
    rulesets = configuration.makeelement('rulesets', attrib)
    configuration.append(rulesets)
    
    # <build><pluginManagement><plugins><plugin><executions><execution><configuration><rulesets><ruleset>
    ruleset = rulesets.makeelement('ruleset', attrib)
    ruleset.text = pmd_xml_rules
    rulesets.append(ruleset)
    
    # <build><pluginManagement><plugins><plugin><executions><execution><configuration><configLocation>
    #configLocation = configuration.makeelement('configLocation', attrib)
    #configLocation.text = pmd_xml_rules
    #configuration.append(configLocation)

    # <build><pluginManagement><plugins><plugin><executions><execution><configuration><encoding>
    encoding = configuration.makeelement('encoding', attrib)
    encoding.text = 'UTF-8'
    configuration.append(encoding)

    # <build><pluginManagement><plugins><plugin><executions><execution><configuration><failsOnError>
    failsOnError = configuration.makeelement('failsOnError', attrib)
    failsOnError.text = 'true'
    configuration.append(failsOnError)

    # <build><pluginManagement><plugins><plugin><executions><execution><configuration><failOnViolation>
    failOnViolation = configuration.makeelement('failOnViolation', attrib)
    failOnViolation.text = 'false'
    configuration.append(failOnViolation)
    
    # <build><pluginManagement><plugins><plugin><executions><execution><configuration><printFailingErrors>
    printFailingErrors = configuration.makeelement('printFailingErrors', attrib)
    printFailingErrors.text = 'true'
    configuration.append(printFailingErrors)


    ###### Append the pom.xml with the 'reporting' pmd configurations #######
    
    #<reporting>
    reporting = root.makeelement('reporting', attrib)
    root.append(reporting)

    #<reporting><plugins>
    plugins = reporting.makeelement('plugins', attrib)
    reporting.append(plugins)

    #<reporting><plugins><plugin>
    plugin = plugins.makeelement('plugin', attrib)
    plugins.append(plugin)

    #<reporting><plugins><plugin><groupId>
    groupId = plugin.makeelement('groupId', attrib)
    groupId.text = 'org.apache.maven.plugins'
    plugin.append(groupId)

    #<reporting><plugins><plugin><artifactId>
    artifactId = plugin.makeelement('artifactId', attrib)
    artifactId.text = maven_pmd_plugin
    plugin.append(artifactId)

    #<reporting><plugins><plugin><version>
    version = plugin.makeelement('version', attrib)
    version.text = maven_pmd_plugin_version
    plugin.append(version)

    #<reporting><plugins><plugin><configuration>
    configuration = plugin.makeelement('configuration', attrib)
    plugin.append(configuration)

    # <reporting><plugins><plugin><configuration><rulesets>
    rulesets = configuration.makeelement('rulesets', attrib)
    configuration.append(rulesets)
    
    # <reporting><plugins><plugin><configuration><rulesets><ruleset>
    ruleset = rulesets.makeelement('ruleset', attrib)
    ruleset.text = pmd_xml_rules
    rulesets.append(ruleset)
    
    #<reporting><plugins><plugin><configuration><configLocation>
    #configLocation = configuration.makeelement('configLocation', attrib)
    #configLocation.text = pmd_xml_rules 
    #configuration.append(configLocation)

    #<reporting><plugins><plugin><configuration><failsOnError>
    failsOnError = configuration.makeelement('failsOnError', attrib)
    failsOnError.text = 'true'
    configuration.append(failsOnError)

    #<reporting><plugins><plugin><configuration><failOnViolation>
    failOnViolation = configuration.makeelement('failOnViolation', attrib)
    failOnViolation.text = 'false'
    configuration.append(failOnViolation)
    
    # <reporting><plugins><plugin><configuration><printFailingErrors>
    printFailingErrors = configuration.makeelement('printFailingErrors', attrib)
    printFailingErrors.text = 'true'
    configuration.append(printFailingErrors)

    #tree.write('pom.xml')
    tree.write(pom_xml)
    
####################################################################
# Creates one or more maven applications depending on your choice #
####################################################################
def create_mvn_app_n_copy_multiple_java_files_to_analyse():
    
    #e.g., my-javacodeanalysis-app0
    app_name_full = '{}{}'.format(app_name_partial, array_id)
    
    #e.g. my-javacodeanalysis-app0
    app_name_full_dest_path = app_name_full
    
    #e.g., ../my_codesnippet_analysis/pmd1/mvn_apps
    #or mvn_apps
    parent_dest_full_path = parent_dest_path
    
    #e.g., ../my_codesnippet_analysis/pmd1/checks_lib
    #or checks_lib
    lib_full_path = '{}/{}'.format(parent_dest_full_path, lib_path)
    
    
    if use_comm_root_dir == True and use_parent_dest_path == True:
        #e.g., ../my_codesnippet_analysis/pmd1/mvn_apps/
        parent_dest_full_path = '{}/{}'.format(comm_root_dir, parent_dest_path)
        #e.g., ../my_codesnippet_analysis/pmd1/checks_lib
        lib_full_path = '{}/{}'.format(comm_root_dir, lib_path)
        #e.g., ../my_codesnippet_analysis/pmd1/mvn_apps/my-javacodeanalysis-app0
        app_name_full_dest_path = '{}/{}/{}'.format(comm_root_dir, parent_dest_path, app_name_full)
        
    elif use_comm_root_dir == True:
        #e.g., ../my_codesnippet_analysis/pmd1/mvn_apps
        parent_dest_full_path = comm_root_dir
        #e.g., ../my_codesnippet_analysis/pmd1/checks_lib
        lib_full_path = '{}/{}'.format(comm_root_dir, lib_path)
        #e.g., ../my_codesnippet_analysis/pmd1/mvn_apps/my-javacodeanalysis-app0
        app_name_full_dest_path = '{}/{}'.format(comm_root_dir, app_name_full)
        
    elif use_parent_dest_path == True:
        #e.g., ../my_codesnippet_analysis/pmd1/mvn_apps/my-javacodeanalysis-app0
        app_name_full_dest_path = '{}/{}'.format(parent_dest_path, app_name_full)
        
        
    #e.g., ../my_codesnippet_analysis/pmd1/mvn_apps/my-javacodeanalysis-app0/src/main/java
    app_name_full_child_dest_path = '{}/{}'.format(app_name_full_dest_path, child_dest_path)
    #e.g., ../my_codesnippet_analysis/pmd1/mvn_apps/my-javacodeanalysis-app0/src/main/java/myjavacodeanalysis
    app_name_full_child_dest_path_pkg = '{}/{}'.format(app_name_full_child_dest_path, java_pkg)
    
    # Rename app if this is true
    if rm_auto_gen_file == True:
        # remove existing directory if they already exist
        #remove_dir_if_exist_cmd = 'cd ../my_codesnippet_analysis/pmd1/mvn_apps/; rm -rf my-javacodeanalysis-app0
        remove_dir_if_exist_cmd = 'cd {}; rm -rf {}'.format(parent_dest_full_path, app_name_full)
        cmd1 = sp.run(
            remove_dir_if_exist_cmd, # command
            capture_output=True,
            text=True,
            shell=True
        )
       
    
    # create mvn app 
    #maven_app_cmd = 'cd ../my_codesnippet_analysis/pmd1/mvn_apps/; mvn archetype:generate -DgroupId=myjavacodeanalysis -DartifactId=my-javacodeanalysis-app0 -DarchetypeArtifactId=maven-archetype-quickstart -DarchetypeVersion=1.4 -DinteractiveMode=false'
    maven_app_cmd = 'cd {}; mvn archetype:generate -DgroupId={} -DartifactId={} -DarchetypeArtifactId=maven-archetype-quickstart -DarchetypeVersion=1.4 -DinteractiveMode=false'.format(parent_dest_full_path, pkg_name_full, app_name_full)
    cmd2 = sp.run(
        maven_app_cmd, # command
        capture_output=True,
        text=True,
        shell=True
    )

    # update pom.xml
    update_pom_xml(app_name_full_dest_path)
    
    # format the pom.xml file and put the result in pom_fmt.xml  
    #e.g., fmt_pom_xml_cmd = 'cd ../my_codesnippet_analysis/pmd1/mvn_appsa/my-javacodeanalysis-app0; xmllint --format pom.xml > pom_fmt.xml'
    fmt_pom_xml_cmd = 'cd {}; xmllint --format pom.xml > pom_fmt.xml'.format(app_name_full_dest_path)
    cmd4 = sp.run(
        fmt_pom_xml_cmd, # command
        capture_output=True,
        text=True,
        shell=True
    )
    
    #remove the pom.xml file 
     #e.g., rv_pom_xml_cmd = 'cd ../my_codesnippet_analysis/pmd1/mvn_appsa/my-javacodeanalysis-app0; rm pom.xml'
    rm_pom_xml_cmd = 'cd {}; rm pom.xml'.format(app_name_full_dest_path)
    cmd5 = sp.run(
        rm_pom_xml_cmd, # command
        capture_output=True,
        text=True,
        shell=True
    )
    
    #rename the pom_fmt.xml to pom.xml file
     #e.g., rm_pom_xml_cmd = 'cd ../my_codesnippet_analysis/pmd1/mvn_appsa/my-javacodeanalysis-app0; mv pom_fmt.xml pom.xml'
    mv_pom_xml_cmd = 'cd {}; mv pom_fmt.xml pom.xml'.format(app_name_full_dest_path)
    cmd6 = sp.run(
        mv_pom_xml_cmd, # command
        capture_output=True,
        text=True,
        shell=True
    )
    
    # Copy the 'pmdrules.xml' from the check_lib to the root dir of app 
    #cp_checks_xml_cmd = 'cp checks_lib/pmdrules.xml ../my_codesnippet_analysis/pmd1/mvn_appsa/my-javacodeanalysis-app0'
    cp_checks_xml_cmd = 'cp {}/{} {}'.format(lib_full_path, pmd_xml_rules, app_name_full_dest_path)
    
    cmd7 = sp.run(
        cp_checks_xml_cmd, # command
        capture_output=True,
        text=True,
        shell=True
    )
    
     
    # Delete the App.java file that is created by default from src/main/java/yourpkgdir
    #e.g., rv_def_java_app_file_cmd = 'rm ../my_codesnippet_analysis/pmd1/mvn_apps/my-javacodeanalysis-app0/src/main/java/myjavacodeanalysis/App.java'
    rm_def_java_app_file_cmd = 'rm {}/{}'.format(app_name_full_child_dest_path_pkg, auto_gen_file_rm)
    cmd8 = sp.run(
        rm_def_java_app_file_cmd, # command
        capture_output=True,
        text=True,
        shell=True
    )
    
    # Copy or Move source code files
    filenames_array_id = split_filenames[int(array_id)]
    print('Array Id: {} Number of files: {}'.format(array_id, len(filenames_array_id)))
    #e.g dest_dir = '../my_codesnippet_analysis/pmd1/mvn_apps/my-javacodeanalysis-app0/src/main/java/myjavacodeanalysis'
    dest_dir = '{}'.format(app_name_full_child_dest_path_pkg)
    if mv_src == True:
        #move a list of file from source to dest
        for file in filenames_array_id:
            shutil.move(file, dest_dir)
    else:
        #copy a list of file from source to dest
        for file in filenames_array_id:
            shutil.copy(file, dest_dir)
    
    #create a status file
    
    


# Create maven app and move files on each process
create_mvn_app_n_copy_multiple_java_files_to_analyse()


print('Done rank {} -:)'.format(array_id))

