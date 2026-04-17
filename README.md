# slide-gen

Project for SC4052 Cloud Computing 
Topic 8: PaaS (Presentation as a Service)

The first version is up. To fully test the code, you will need the gcp-credentials.json, which can be generated from your google cloud by going to the IAM Permissions, creating a Vertex AI User and copy pasting the gcp-credentials.json file into the server_gen_vertex folder. 

After that, you can use the command to build everything
```
docker compose up --build
```

The features are allwoing users to upload a text or PDF prompt to allow AI to generate slides. demo on youtube [here](https://www.youtube.com/watch?v=Ew0wn8b7hmk)

## Development stuff

To build each of the servers or client separately, just use the folder name behind the above command
```
docker compose up --build client
```
```
docker compose up --build server_gen_vertex
```
```
docker compose up --build server_build
```

## Acknowledgements
The [PptxGenJS](https://github.com/gitbrent/PptxGenJS) library was a very important part of this project. I also used Claude and Gemini to generate ideas, edit and make some code and then tried to make it as streamlined as possible. The Google Cloud Vertex AI free trial for students was also useful. 

## Experimental stuff
From now on all changes will mostly be experimental changes I will be testing in another branch. I think getting the AI to understand a bit of colour theory to ensure the text is easier to read and more aesthetically pleasing. Some other ideas are to integrate the promising looking [pptx-automizer](https://github.com/singerla/pptx-automizer) into server_build to allow users to upload their own powerpoint template and then insert elements. Integrating image APIs or image generation to iclude in the presentation would also be a good direction, and interatively editing the generated powerpoint within the chatbot would also be a useful features. Maybe integration with WebLLM or Nemobot. 
