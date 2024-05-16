"use client";
import React, { useEffect, useState } from 'react';
import AWS from "aws-sdk";
import axios from 'axios';


const S3_BUCKET = '<>';
const REGION = '<>';
const ACCESS_KEY_ID = '<ACCESS KEY>';
const SECRET_ACCESS_KEY = '<SECRET>';



const FileUploadPage: React.FC = () => {
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [responseData , setresponseData] = useState<any>(null);

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files && event.target.files.length > 0) {
          setSelectedFile(event.target.files[0]);
        }
      };
    
      const handleUpload = async () => {
        if (!selectedFile) {
          console.error('No file selected.');
          return;
        }
    
        const s3 = new AWS.S3({
          accessKeyId: ACCESS_KEY_ID,
          secretAccessKey: SECRET_ACCESS_KEY,
          region: REGION,
        });
    
        const params = {
          Bucket: S3_BUCKET,
          Key: selectedFile.name,
          Body: selectedFile,
          ACL:'public-read'
        };
    
        try {
          await s3.upload(params).promise();
          var link = "<>"+selectedFile.name;
            try {
                const response = await axios.post('http://127.0.0.1:8000/file-upload/upload/',{ "pdf_url": link });
                if(response.status == 200){
                    setresponseData(response.data);
                }
            } catch (error) {
                alert("Internal Server Error!")
                // console.error('Error sending link to backend:', error);
            }
            

        } catch (error) {
          console.error('Error uploading file to S3:', error);
        }
      };


  return (
    <div className="bg-black min-h-screen">
        <div className='flex flex-col items-center pt-40'>
            <h1 className="text-2xl font-bold text-white mb-4">Upload The Resume Here</h1>
            <div className='pt-10'>
            <input type="file" accept=".pdf" onChange={handleFileChange} className=" disabled:opacity-50 disabled:bg-red-50 disabled:border disabled:border-red-500 
                  disabled:text-red-900 disabled:placeholder-red-700 disabled:text-sm disabled:rounded-lg 
                  disabled:focus:ring-red-500 disabled:dark:bg-gray-700 disabled:focus:border-red-500 
                  disabled:block disabled:w-full  disabled:dark:text-red-500 disabled:dark:placeholder-red-500
                  disabled:dark:border-red-500
                  block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer 
                  bg-gray-50 dark:text-gray-400 focus:outline-none dark:bg-gray-700 
                  dark:border-gray-600 dark:placeholder-gray-400" />
            <div className='flex justify-center pt-10'>
                <button onClick={handleUpload} className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded">
                    Submit
                </button>
            </div>
            </div>
            {responseData && (
            <div className="text-white mt-4">
                <pre>{JSON.stringify(responseData, null, 2)}</pre>
            </div>
            )}
        </div>
    </div>
  );
};

export default FileUploadPage;
