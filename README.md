# image-gen

# Run test client on its own (not connected to API)

```
cd client_streamlit
```
```
pip install -r requirements.txt
```
```
streamlit run app.py
```  

# Setup before running server on docker (Important)
Important: You need at least 48 GB of RAM to run this because Stable Diffusion eats 20GB already

- Download WSL 2 Ubuntu 22.04 from Windows Store https://apps.microsoft.com/detail/9pn20msr04dw?hl=en-US&gl=US  
- Download docker desktop https://www.docker.com/products/docker-desktop/  
- Create a file in C:/Users/YourUsername/.wslconfig (the file is called .wslconfig in the directory and write (or copy paste)  

```
[wsl2]    
memory=32GB  # Max RAM WSL2/Docker can use    
processors=4  # Number of CPUs`    
swap=8GB  # Swap file size    
localhostForwarding=true
```  

to allow stable diffusion to eat all your system memory   

# Run server on docker
Important: You need the folders of the models namely: 
- gemma-3-12b-it 

## Install models like this:  
### Get the token for the auth step
[Official Documentation](https://huggingface.co/docs/hub/en/security-tokens)  **Note: Apply for a read token**
### Make sure you have been granted access for all the models
- gemma-3-12b-it (in server_slidedeckai)  
Visit the link and click access gated models at the top (they are all gated). Also just the model links for reference  
[gemma-3-12b-it](https://huggingface.co/google/gemma-3-12b-it)    
[tensorblock/gemma-3-12b-it-GGUF](https://huggingface.co/tensorblock/gemma-3-12b-it-GGUF)  
### Download huggingface cli
```
pip install -U "huggingface_hub[cli]"
```
### Verify installation
```
hf --help
```
### Login with your auth token which you got earlier
```
hf auth login
```
### Download the models
```
hf download tensorblock/gemma-3-12b-it-GGUF \
  --include "gemma-3-12b-it-Q4_K_M.gguf" \
  --local-dir ./models/gemma-3-12b-it/
```
# Docker command to run server_slidedeckai
```
docker compose up --build server_slidedeckai
```

(for stable diffusion image generation model)  
Wait for stable diffusion image generation model to load after `Loading slide deck model (gemma-3-12b-it)...` logged in your terminal  (actally seems ok since downloaded)  
Open task manager and watch all your memory get eaten by gemma-3-12b-it-GGUF 

# Create network for containers to communicate to one another  
```
docker network create vision_network
```    
Important so that frontend can talk to backend  

# Containerization of Server Slide Deck AI (No Internet)
### Make sure the docker image for generation and edit is built without the annoying cache: 
```
docker compose build --no-cache server_slidedeckai
```
**After this step, if you don't care about saving the image to a tar file to use on another device, it is ok to skip to the run step**  
### Save the docker images (slides) to a tar file 
```
docker save -o server_slidedeckai.tar server_slidedeckai
```  
(takes up a lot of CPU and RAM, takes 30+ minutes)  

**Note: Only load when on a different device**  
### Load the docker image (slides): 
```
docker load -i server_slidedeckai.tar
```      

### Run the docker image (slides): 
```
docker run --name fastapislides--network vision_network --rm -p 8002:8002 --gpus all server_slidedeckai
```
(Note: --rm to keep system clean after exit, --gpus all to make sure there is GPU access, -p to expose the right port)  

### Remove messy cache stuff (I hope): 
```
docker system prune -a --volumes
```      

# Containerization of Client (No Internet)  
### Make sure the docker image is built without the annoying cache: 
```
docker compose build --no-cache streamlit
```    
### Save the docker image to a tar file 
```
docker save -o streamlit.tar streamlit
```

Note: Only load when on a different device  
### Load the docker image: 
```
docker load -i streamlit.tar
```     
### Run the docker image: 
```
docker run --name streamlit --network vision_network  --rm -p 8501:8501 streamlit
``` 

# More Documentaion
In case you want a diagram of how things should work refer to slides_gen_diagram.pdf
