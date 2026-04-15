frappe.listview_settings['Task'] = { // Change 'Task' to your DocType
    refresh: function(list_view) {
        console.log("script Loaded");
        
        // if (listview.view_name === 'Gantt') {
            list_view.page.add_inner_button(__('Export Full Gantt'), function() {
                export_gantt_as_image();
            });
        // }
    }
};

function export_gantt_as_image() {
    const svg = document.querySelector(".gantt-container svg");
    if (!svg) {
        frappe.msgprint(__("No Gantt chart found."));
        return;
    }

    const clonedSvg = svg.cloneNode(true);
    
    // 1. Sync the individual bar colors (Status Mapping)
    const originalBars = svg.querySelectorAll(".bar-group");
    const clonedBars = clonedSvg.querySelectorAll(".bar-group");

    originalBars.forEach((bar, index) => {
        const progress = bar.querySelector(".bar-progress");
        const mainBar = bar.querySelector(".bar");
        
        if (progress && clonedBars[index]) {
            const color = window.getComputedStyle(progress).fill;
            const clonedProgress = clonedBars[index].querySelector(".bar-progress");
            if (clonedProgress) clonedProgress.style.fill = color;
        }
        
        if (mainBar && clonedBars[index]) {
            const bgColor = window.getComputedStyle(mainBar).fill;
            const clonedMain = clonedBars[index].querySelector(".bar");
            if (clonedMain) clonedMain.style.fill = bgColor;
        }
    });

    // 2. Inject CSS to fix arrows, hide handles, and REMOVE the Today line
    const style = document.createElement("style");
    style.innerHTML = `
        /* Remove the thick black today-indicator line */
        .today-highlight { display: none !important; }

        /* Hide the resize handles (the black bars at the ends) */
        .handle-group { display: none !important; }
        
        /* Ensure arrows are lines, not black triangles */
        .arrow { 
            fill: none !important; 
            stroke: #666 !important; 
            stroke-width: 1.2; 
        }
        
        /* Grid and Background */
        .grid-header { fill: #ffffff; stroke: #f0f0f0; }
        .grid-row { fill: #ffffff; }
        .row-line { stroke: #f0f0f0; stroke-width: 1; }
        .tick { stroke: #e0e0e0; stroke-width: 1; }
        
        /* Text Styling */
        .lower-text { font-size: 10px; fill: #888; font-family: sans-serif; }
        .upper-text { font-size: 12px; fill: #333; font-weight: bold; font-family: sans-serif; }
        .bar-label { fill: #333; font-size: 11px; font-family: sans-serif; }
        
        /* General cleanup */
        path { fill: none; } 
        .bar { stroke-width: 0; }
    `;
    clonedSvg.prepend(style);

    // 3. Dimensions
    const bbox = svg.getBBox();
    const width = bbox.width + 60;
    const height = bbox.height + 60;

    const serializer = new XMLSerializer();
    const source = serializer.serializeToString(clonedSvg);

    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const context = canvas.getContext("2d");

    const img = new Image();
    const svgBlob = new Blob([source], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(svgBlob);

    img.onload = function() {
        context.fillStyle = "white";
        context.fillRect(0, 0, width, height);
        context.drawImage(img, 0, 0);
        
        const pngUrl = canvas.toDataURL("image/png");
        const downloadLink = document.createElement("a");
        downloadLink.href = pngUrl;
        downloadLink.download = `gantt_final_report.png`;
        downloadLink.click();
        URL.revokeObjectURL(url);
    };

    img.src = url;
}


// frappe.listview_settings['Task'] = {
//     refresh: function(list_view) {
//         // Clear buttons to prevent duplicates on refresh
//         list_view.page.remove_inner_button(__('Export PNG'));
//         list_view.page.remove_inner_button(__('Open SVG in New Tab'));

//         if (list_view.view_name === 'Gantt') {
//             // Button 1: The PNG Download
//             list_view.page.add_inner_button(__('Export PNG'), function() {
//                 export_gantt_as_image('png');
//             });

//             // Button 2: Open SVG in New Tab
//             list_view.page.add_inner_button(__('Open SVG in New Tab'), function() {
//                 export_gantt_as_image('svg');
//             });
//         }
//     }
// };

// function export_gantt_as_image(format = 'png') {
//     const svg = document.querySelector(".gantt-container svg");
//     if (!svg) {
//         frappe.msgprint(__("No Gantt chart found."));
//         return;
//     }

//     const clonedSvg = svg.cloneNode(true);
    
//     // 1. Sync the individual bar colors (Status Mapping)
//     const originalBars = svg.querySelectorAll(".bar-group");
//     const clonedBars = clonedSvg.querySelectorAll(".bar-group");

//     originalBars.forEach((bar, index) => {
//         const progress = bar.querySelector(".bar-progress");
//         const mainBar = bar.querySelector(".bar");
        
//         if (progress && clonedBars[index]) {
//             const color = window.getComputedStyle(progress).fill;
//             const clonedProgress = clonedBars[index].querySelector(".bar-progress");
//             if (clonedProgress) clonedProgress.style.fill = color;
//         }
        
//         if (mainBar && clonedBars[index]) {
//             const bgColor = window.getComputedStyle(mainBar).fill;
//             const clonedMain = clonedBars[index].querySelector(".bar");
//             if (clonedMain) clonedMain.style.fill = bgColor;
//         }
//     });

//     // 2. Inject CSS for clean export
//     const style = document.createElement("style");
//     style.innerHTML = `
//         .today-highlight { display: none !important; }
//         .handle-group { display: none !important; }
//         .arrow { fill: none !important; stroke: #666 !important; stroke-width: 1.2; }
//         .grid-header { fill: #ffffff; stroke: #f0f0f0; }
//         .grid-row { fill: #ffffff; }
//         .row-line { stroke: #f0f0f0; stroke-width: 1; }
//         .tick { stroke: #e0e0e0; stroke-width: 1; }
//         .lower-text { font-size: 10px; fill: #888; font-family: sans-serif; }
//         .upper-text { font-size: 12px; fill: #333; font-weight: bold; font-family: sans-serif; }
//         .bar-label { fill: #333; font-size: 11px; font-family: sans-serif; }
//         path { fill: none; } 
//         .bar { stroke-width: 0; }
//     `;
//     clonedSvg.prepend(style);

//     // 3. Prepare the Source
//     const bbox = svg.getBBox();
//     // Add viewBox so the SVG knows its own boundaries when opened in a new tab
//     clonedSvg.setAttribute("viewBox", `${bbox.x} ${bbox.y} ${bbox.width} ${bbox.height}`);
//     clonedSvg.setAttribute("width", bbox.width);
//     clonedSvg.setAttribute("height", bbox.height);

//     const serializer = new XMLSerializer();
//     const source = serializer.serializeToString(clonedSvg);
//     const svgBlob = new Blob([source], { type: "image/svg+xml;charset=utf-8" });
//     const url = URL.createObjectURL(svgBlob);

//     if (format === 'svg') {
//         // OPEN IN NEW TAB
//         const newTab = window.open();
//         newTab.document.write(`<title>Gantt Export</title><img src="${url}" style="width:100%;">`);
//     } else {
//         // DOWNLOAD AS PNG
//         const canvas = document.createElement("canvas");
//         canvas.width = bbox.width + 60;
//         canvas.height = bbox.height + 60;
//         const context = canvas.getContext("2d");

//         const img = new Image();
//         img.onload = function() {
//             context.fillStyle = "white";
//             context.fillRect(0, 0, canvas.width, canvas.height);
//             context.drawImage(img, 0, 0);
            
//             const pngUrl = canvas.toDataURL("image/png");
//             const downloadLink = document.createElement("a");
//             downloadLink.href = pngUrl;
//             downloadLink.download = `gantt_${frappe.datetime.now_datetime()}.png`;
//             downloadLink.click();
//             URL.revokeObjectURL(url);
//         };
//         img.src = url;
//     }
// }