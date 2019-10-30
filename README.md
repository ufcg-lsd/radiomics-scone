# ISSRE '19 - Building Applications for Trustworthy Data Analysis in the Cloud

This application is a use case from the EU-Brazil Atmosphere project. For more information on the project, visit our website at [https://www.atmosphere-eubrazil.eu/](https://www.atmosphere-eubrazil.eu/). The original application is hosted at the project's GitHub repository at [https://github.com/eubr-atmosphere/radiomics](https://github.com/eubr-atmosphere/radiomics). More details about SCONE can also be found at [https://sconedocs.github.io](https://sconedocs.github.io).

## Radiomics Approach

This application focuses on the implementation of the pilot application on Medical Imaging Biomarkers. This radiomics approach includes a processing pipeline to extract frames from videos, classify them, select those frames with significative data, filter them and extract image features using first- and second-order texture analysis and image computing. Finally, that pipeline concludes a classification (normal, definite or borderline RHD). 

### Functions

* main: Main pipeline
* anonymise: **frame extraction and anonymization pipeline** 
* video_frame: Read video frame and detect doppler ones
* view_classification: Classify video frames into the different view classes:
  * 0: 4 chamber
  * 1: Parasternal Short Axis
  * 2: Parasternal Long Axis
* doppler_segmentation: Apply a color-based segmentation to extract the colors from the doppler images using a k-means clustering
* texture_analysis: Perform first- and second-order texture analysis for image characterization and extraction of maximum blood velocities
* texture_classification: Conclude a classification (normal, borderline or definite RHD) according to the image features

### Folders
 
* classifiers: includes files needed for the view classifier and for the textures classification
* sample-videos: contains sample videos to be processed

### Usage

For this demonstrator, the *anonymise* pipeline will be ran.

```bash
$ python anonymise.py -i inputfolder -o outputfolder 
```

## 1) Running on SCONE

To run the application on SCONE environment, run the following the steps: 

### Step 1.1: Build the image

```bash
$ docker build -t sconecuratedimages/issre2019:runtime-radiomics .
Sending build context to Docker daemon  240.6MB
Step 1/13 : FROM sconecuratedimages/issre2019:tensorscone as tensorscone
 ---> 83847162d638

...

Step 13/13 : ENV SCONE_ALLOW_DLOPEN=2
 ---> Using cache
 ---> 012132609114
Successfully built 012132609114
Successfully tagged sconecuratedimages/issre2019:runtime-radiomics
```

### Step 1.2: Running the application

For the instance, we are using as input a set of sample videos on **'sample-videos/'** folder and saving the anonymized frames on **'output/'**. 

```bash
$ docker run --device /dev/isgx --volume $PWD/sample-videos:/mnt/input --volume $PWD/output:/mnt/output --volume $PWD/app:/app --workdir /app -t sconecuratedimages/issre2019:runtime-radiomics python anonymise.py -i /mnt/input -o /mnt/output
```

Follows a brief explanation of used arguments:

* *run*: run a command on a new container.
* *--device /dev/isgx*: expose the /dev/isgx - Intel(r) SGX device - to the container.
* *--volume $PWD/sample-videos:/mnt/input*: mount the 'sample-videos' folder to '/mnt/input' mount point on container.
* *--workdir /app*: starts the container using /app as current working directory.
* *-t*: allocate a pseudo-TTY to show the application output on screen.
* *sconecuratedimages/issre2019:runtime-radiomics*: container name:tag.
* *python anonymise.py -i /mnt/input -o /mnt/output*: command to execute on container.

Note: if there's no available Intel(r) SGX on the machine, just remove *--device /dev/isgx* from command line. If you want to force the execution using SGX simulation mode, set SCONE_MODE=SIM (--env SCONE_MODE=SIM).

## 2) Enabling SCONE File Protection

SCONE supports the transparent encryption and/or authentication of files. By transparent, we mean that there are no application code changes needed to support this. To demonstrate this feature on our current application, we will extend the base image (created on [step 1.1](#step-11-build-the-image)), using both authentication and encryption features. See more in [SCONE File Protection](https://sconedocs.github.io/SCONE_Fileshield/).

### Step 2.1: Build the FSPF-enabled image

To build the image, execute the command:

```bash
$ docker build --no-cache -f Dockerfile-fspf -t sconecuratedimages/issre2019:radiomics-fspf .
```

During the build process, the file system protection file ('fspf.pb') will be encrypted using AES-GCM mode and both tag & key will be printed on the screen. Write these keys down on a safe place, both will be required to execute the application on the next steps. The key and tag appears on the following format:

```bash
Encrypted file system protection file fspf.pb AES-GCM tag: 1efedbc94a1da5182c252958a13a245c key: 7fcefa090c73d93d47a20ad603ec5766e3537ac09b9b74b919ee9e5c5a9ba50b
```

The FSPF protections used on this example includes application code encryption (code confidentiality) and system files authentication (which incldes libraries). Check 'Dockerfile-fspf' for details on how it was done.

### Step 2.2: Running the application with FSPF

To run the FSPF-enabled application, we need to inform to the application the AES-GCM tag, key & path of the 'fspf.pb' protection file. To make this locally (without a Configuration & Attestation Service), environment variables are used. We are using the same sample videos and output path '/output-fspf'.

```bash
$ export FSPF_TAG=1efedbc94a1da5182c252958a13a245c
$ export FSPF_KEY=7fcefa090c73d93d47a20ad603ec5766e3537ac09b9b74b919ee9e5c5a9ba50b
$ export FSPF_PATH=/fspf.pb
$ docker run --device /dev/isgx --volume $PWD/sample-videos:/mnt/input --volume $PWD/output-fspf:/mnt/output --env SCONE_FSPF=$FSPF_PATH --env SCONE_FSPF_TAG=$FSPF_TAG --env SCONE_FSPF_KEY=$FSPF_KEY -t sconecuratedimages/issre2019:radiomics-fspf python anonymise.py -i /mnt/input -o /mnt/output
```

Note: if there's no available Intel(r) SGX on the machine, just remove *--device /dev/isgx* from command line. If you want to force the execution using SGX simulation mode, set SCONE_MODE=SIM (--env SCONE_MODE=SIM).

## 3) Using FSPF for input files

At this point, we have code confidentiality and system files authentication, but input files are still 'readeable'. Through the use of SCONE configuration & attestation service (a.k.a Palaemon), the user is able to provide secrets to be read by the application. A remote attestation process ensures that secrets will only be delivered to authorized applications. Details about Configuration & Attestation are found [here](https://sconedocs.github.io/CASOverview/).

### Step 3.1: Creating FSPF volume for input files

At this step, we will encrypt our set of sample videos ('/sample-videos') and store it on '/encrypted-videos' folder. To initialize the filesystem protection file, run:

```bash
$ docker run -v $PWD/sample-videos:/mnt/input-original -v $PWD/encrypted-videos:/mnt/input --workdir /mnt/input --rm sconecuratedimages/issre2019:runtime-alpine3.7 /bin/bash -c "scone fspf create volume.fspf"
Created empty file system protection file in volume.fspf. AES-GCM tag: cf84563e0ef7901a899ff0c599812358
```

Then, create an encrypted kernel region using '.' as path. The region '.' (meaning current directory) is mandatory on volumes where keys are provided by the Palaemon.

```bash
$ docker run -v $PWD/sample-videos:/mnt/input-original -v $PWD/encrypted-videos:/mnt/input --workdir /mnt/input --rm sconecuratedimages/issre2019:runtime-alpine3.7 /bin/bash -c "scone fspf addr volume.fspf . --encrypted --kernel ."
Added region . to file system protection file volume.fspf new AES-GCM tag: 02de46ae3cab5f029e09e7ea76e4c3d1
```

Now, add the files to encrypted volume. The next command that will be îssued encrypt and write files on destination folder.

```bash
$ docker run -v $PWD/sample-videos:/mnt/input-original -v $PWD/encrypted-videos:/mnt/input --workdir /mnt/input --rm sconecuratedimages/issre2019:runtime-alpine3.7 /bin/bash -c "scone fspf addf volume.fspf . /mnt/input-original /mnt/input"
Added files to file system protection file volume.fspf new AES-GCM tag: c67a123e037f6b6495dde497ea040194
```

To finish the volume creation process, encrypt the 'volume.fspf' itself.

```bash
$ docker run -v $PWD/sample-videos:/mnt/input-original -v $PWD/encrypted-videos:/mnt/input --workdir /mnt/input --rm sconecuratedimages/issre2019:runtime-alpine3.7 /bin/bash -c "scone fspf encrypt volume.fspf"
Encrypted file system protection file volume.fspf AES-GCM tag: 9737584f495a4c5af9ea5cd5d36daba1 key: 74cc3802b19c62f555332f7dea8d323c55f90ed4aa287b90fdfcf1c6a8ea611b
```

Like occurs during image build process described on step 2.1, the volume key & tag are necessary to open the volume for transparent encryption RW operations managed by SCONE.

### Step 3.2: Creating the Palaemon session

An enclave is identified by a hash value which is called MRENCLAVE. Before start the creation of Palaemon session, first we need to determine the [MRENCLAVE](https://sconedocs.github.io/MrEnclave/) of Python interpreter.

```bash
$ docker run --rm --env SCONE_VERSION=1 -it sconecuratedimages/issre2019:radiomics-fspf python -c "exit" | grep "Enclave hash"
Enclave hash: 5a30153e87e3067912b92f5126731136f3b3b84550dde5645887db356e0ae63d
```

Then, copy & paste the content from the block bellow into a file called 'session.yml', replacing the content delimited by < > symbols with the corresponding information.

```
name: issre-tutorial-<firstname_lastname>
digest: create
predecessor: null

services:
   - name: radiomics
     image_name: sconecuratedimages/issre2019:radiomics-fspf
     mrenclaves: [<python mrenclave - from step 3.2>]
     command: python2.7 -B anonymise.py -i /mnt/input -o /mnt/output
     pwd: /app
     tags: [demo]
     fspf_tag: <image fspf tag - from step 2.1>
     fspf_key: <image fspf key - from step 2.1>
     fspf_path: /fspf.pb

volumes:
    - name: input-videos
      fspf_tag: <volume fspf tag - from step 3.1 (last command output)>
      fspf_key: <volume fspf key - from step 3.1 (last command output)>

images:
   - name: sconecuratedimages/issre2019:radiomics-fspf
     mrenclaves: [<python mrenclave - from step 3.2>]
     tags: [demo]
     volumes:
       - name: input-videos
         path: /mnt/input
```

For the instance, the resulting 'session.yml' using the example keys & tags is:

```
name: issre-tutorial-fabio_silva
digest: create
predecessor: null

services:
   - name: radiomics
     image_name: sconecuratedimages/issre2019:radiomics-fspf
     mrenclaves: [5a30153e87e3067912b92f5126731136f3b3b84550dde5645887db356e0ae63d]
     command: python2.7 -B anonymise.py -i /mnt/input -o /mnt/output
     pwd: /app
     tags: [demo]
     fspf_tag: 47c3cd24ebdfa456fd95025b28538dcd
     fspf_key: 4a290efa0ffed54d34e8e404f01f81f06ad9dce38b4d5314bbbef2cb9056d8ea
     fspf_path: /fspf.pb

volumes:
    - name: input-videos
      fspf_tag: 9737584f495a4c5af9ea5cd5d36daba1
      fspf_key: 74cc3802b19c62f555332f7dea8d323c55f90ed4aa287b90fdfcf1c6a8ea611b

images:
   - name: sconecuratedimages/issre2019:radiomics-fspf
     mrenclaves: [5a30153e87e3067912b92f5126731136f3b3b84550dde5645887db356e0ae63d]
     tags: [demo]
     volumes:
       - name: input-videos
         path: /mnt/input
```

Then save on a file named 'session.yaml'.

### Step 3.3: Create a Client Certificate

To interact with CAS, we need to create a client certificate. When we create a session, it is associated with the client certificate of the creator. Any access to this session requires that the client knows the private key of the client certificate.

Let's create a client certificate without a password. Note that you would typically add a password!

```bash
$ mkdir -p conf
$ if [[ ! -f conf/client.crt || ! -f conf/client-key.key  ]] ; then
        openssl req -new -newkey rsa:4096 -days 365 -nodes -x509 -subj "/C=EU/ST=CAS/L=CLIENT/O=Internet/CN=scontain.com" -out conf/client.crt -keyout conf/client-key.key
  fi
```

Now we have both 'conf/client-key.key' key and 'conf/client.crt' certificate.

### Step 3.4: Upload the session

For this tutorial, we are using a Palaemon instance listening on address 'scone.lsd.ufcg.edu.br:8081'. To publish the session, run the following command:

```bash
$ curl -k -s --cert conf/client.crt --key conf/client-key.key --data-binary @session.yml -X POST https://scone.lsd.ufcg.edu.br:8081/session
Created Session[id=9cfc9694-321b-4f85-9a79-b576376f06c4, name=issre-tutorial-fabio_silva, status=Pending]
```

Done! Now we have our secrets provisioned on a Palaemon session. If you wish to read the provisioned secrets, you can run:
```bash
$ curl -k -s --cert conf/client.crt --key conf/client-key.key --data-binary @session.yml -X GET https://scone.lsd.ufcg.edu.br:8081/session/issre-tutorial-fabio_silva

---
name: issre-tutorial-fabio_silva
digest: eb4810eee9a419d315169f3736a4e180bf3f4a84c0602e960a0dbce7878d5fcc
board_members: []
board_policy:
  minimum: 0
  timeout: 30
images:
  - name: "sconecuratedimages/issre2019:radiomics-fspf"
    mrenclaves:
      - 5a30153e87e3067912b92f5126731136f3b3b84550dde5645887db356e0ae63d
    tags:
      - demo
    volumes:
      - name: input-videos
        path: /mnt/input
services:
  - name: radiomics
    image_name: "sconecuratedimages/issre2019:radiomics-fspf"
    tags:
      - demo
    mrenclaves:
      - 5a30153e87e3067912b92f5126731136f3b3b84550dde5645887db356e0ae63d
    command: python2.7 -B anonymise.py -i /mnt/input -o /mnt/output
    pwd: /app
    fspf_path: /fspf.pb
    fspf_key: 4a290efa0ffed54d34e8e404f01f81f06ad9dce38b4d5314bbbef2cb9056d8ea
    fspf_tag: 47c3cd24ebdfa456fd95025b28538dcd
volumes:
  - name: input-videos
    fspf_tag: 9737584f495a4c5af9ea5cd5d36daba1
    fspf_key: 74cc3802b19c62f555332f7dea8d323c55f90ed4aa287b90fdfcf1c6a8ea611b
```
### Step 3.5: Start the Local Attestation Serive

LAS is need to perform a local attestation (i.e., this creates a quote that can be verified by CAS). To start the LAS, run:

```bash
$ docker run -d -p 18766:18766 --device /dev/isgx:/dev/isgx --name radiomics-las --rm sconecuratedimages/issre2019:las
```

### Step 3.6: Running the Application

After entire process of encrypting volumes, creating a session, provisioning it on CAS, now we are able to start the application:

```bash
$ docker run --device /dev/isgx --volume $PWD/encrypted-videos:/mnt/input --volume $PWD/output-anonymized:/mnt/output --env SCONE_CAS_ADDR=scone.lsd.ufcg.edu.br --env SCONE_LAS_ADDR=172.17.0.1:18766 --env SCONE_CONFIG_ID=issre-tutorial-fabio_silva/radiomics -t sconecuratedimages/issre2019:radiomics-fspf python
```

Follows a brief explanation of used environment variables:

* *SCONE_CAS_ADDR*: the address where Palaemon is listening.
* *SCONE_LAS_ADDR*: the address of Local Attestation Service.
* *SCONE_CONFIG_ID*: contains the identifier of application configuration. It follows the format: session-name/service-name

Note: To execute the application that supports the mount of multiple FSPF volumes, is mandatory the use of Palaemon, which means that you NEED to run the application enclave in SGX hardware mode (SCONE_MODE=HW). It occurs because the Palaemon verifies a quote generated by LAS, and it uses processor embedded features to measure this.
